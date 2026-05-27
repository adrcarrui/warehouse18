from __future__ import annotations

import json
import os
import socket
import time
from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import SessionLocal


POLL_SECONDS = int(os.getenv("WAREHOUSE_READER_HEALTH_POLL_SECONDS", "10"))
CONNECT_TIMEOUT_SECONDS = float(os.getenv("WAREHOUSE_READER_CONNECT_TIMEOUT_SECONDS", "2"))
FAILURES_BEFORE_OFFLINE = int(os.getenv("WAREHOUSE_READER_FAILURES_BEFORE_OFFLINE", "3"))


def tcp_check(host: str, port: int) -> tuple[bool, str | None]:
    try:
        with socket.create_connection((host, port), timeout=CONNECT_TIMEOUT_SECONDS):
            return True, None
    except Exception as exc:
        return False, str(exc)


def insert_connectivity_event(
    db: Session,
    *,
    reader_id: str,
    event_type: str,
    status_from: str | None,
    status_to: str,
    error: str | None = None,
) -> None:
    db.execute(
        text("""
            INSERT INTO rfid_reader_connectivity_events (
                reader_id,
                event_type,
                status_from,
                status_to,
                error,
                checked_at
            )
            VALUES (
                CAST(:reader_id AS TEXT),
                CAST(:event_type AS TEXT),
                CAST(:status_from AS TEXT),
                CAST(:status_to AS TEXT),
                CAST(:error AS TEXT),
                now()
            )
        """),
        {
            "reader_id": reader_id,
            "event_type": event_type,
            "status_from": status_from,
            "status_to": status_to,
            "error": error,
        },
    )


def ensure_offline_alert(
    db: Session,
    *,
    reader_id: str,
    name: str,
    host: str,
    port: int,
    error: str,
) -> None:
    metadata = json.dumps(
        {
            "reader_id": reader_id,
            "name": name,
            "host": host,
            "port": port,
            "error": error,
        },
        ensure_ascii=False,
    )

    result = db.execute(
        text("""
            INSERT INTO alerts (
                code,
                title,
                message,
                severity,
                status,
                source,
                entity_type,
                entity_id,
                metadata,
                created_at,
                updated_at
            )
            VALUES (
                'RFID_READER_OFFLINE',
                'RFID reader offline',
                CAST(:message AS TEXT),
                'critical',
                'open',
                'rfid',
                'reader',
                CAST(:reader_id AS TEXT),
                CAST(:metadata AS JSONB),
                now(),
                now()
            )
            ON CONFLICT (code, entity_id)
            WHERE code = 'RFID_READER_OFFLINE'
              AND status = 'open'
            DO UPDATE SET
                message = EXCLUDED.message,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            RETURNING id, created_at, updated_at
        """),
        {
            "reader_id": reader_id,
            "metadata": metadata,
            "message": (
                f"RFID reader '{name}' ({host}:{port}) is not reachable. "
                f"Last error: {error}"
            ),
        },
    ).mappings().first()

    if result:
        print(
            f"[reader-health] alert upserted | reader_id={reader_id} "
            f"alert_id={result['id']} created_at={result['created_at']} "
            f"updated_at={result['updated_at']}"
        )


def resolve_offline_alert(db: Session, *, reader_id: str) -> None:
    result = db.execute(
        text("""
            UPDATE alerts
            SET
                status = 'resolved',
                resolved_at = now(),
                updated_at = now()
            WHERE code = 'RFID_READER_OFFLINE'
              AND entity_type = 'reader'
              AND entity_id = CAST(:reader_id AS TEXT)
              AND status = 'open'
            RETURNING id
        """),
        {"reader_id": reader_id},
    ).mappings().first()

    if result:
        print(
            f"[reader-health] alert resolved | reader_id={reader_id} "
            f"alert_id={result['id']}"
        )


def check_readers(db: Session) -> None:
    readers = db.execute(
        text("""
            SELECT
                reader_id,
                name,
                host,
                port,
                status,
                consecutive_failures
            FROM rfid_readers
            WHERE is_active IS TRUE
            ORDER BY reader_id
        """)
    ).mappings().all()

    for reader in readers:
        reader_id = reader["reader_id"]
        name = reader["name"]
        host = reader["host"]
        port = int(reader["port"])
        old_status = reader["status"] or "unknown"
        current_failures = int(reader["consecutive_failures"] or 0)

        ok, error = tcp_check(host, port)

        print(
            f"[reader-health] check | reader_id={reader_id} "
            f"ok={ok} old_status={old_status} "
            f"current_failures={current_failures}"
        )

        if ok:
            if old_status != "online":
                insert_connectivity_event(
                    db,
                    reader_id=reader_id,
                    event_type="online",
                    status_from=old_status,
                    status_to="online",
                    error=None,
                )

            db.execute(
                text("""
                    UPDATE rfid_readers
                    SET
                        status = 'online',
                        consecutive_failures = 0,
                        last_healthcheck_at = now(),
                        last_ok_at = now(),
                        last_error = NULL,
                        updated_at = now()
                    WHERE reader_id = CAST(:reader_id AS TEXT)
                """),
                {"reader_id": reader_id},
            )

            resolve_offline_alert(db, reader_id=reader_id)

        else:
            next_failures = current_failures + 1
            next_status = (
                "offline"
                if next_failures >= FAILURES_BEFORE_OFFLINE
                else "degraded"
            )

            if next_status != old_status:
                insert_connectivity_event(
                    db,
                    reader_id=reader_id,
                    event_type=next_status,
                    status_from=old_status,
                    status_to=next_status,
                    error=error,
                )

            db.execute(
                text("""
                    UPDATE rfid_readers
                    SET
                        status = CAST(:status AS TEXT),
                        consecutive_failures = :consecutive_failures,
                        last_healthcheck_at = now(),
                        last_error = CAST(:last_error AS TEXT),
                        updated_at = now()
                    WHERE reader_id = CAST(:reader_id AS TEXT)
                """),
                {
                    "reader_id": reader_id,
                    "status": next_status,
                    "consecutive_failures": next_failures,
                    "last_error": error,
                },
            )

            print(
                f"[reader-health] failure | reader_id={reader_id} "
                f"next_status={next_status} failures={next_failures} "
                f"error={error}"
            )

            if next_status == "offline":
                ensure_offline_alert(
                    db,
                    reader_id=reader_id,
                    name=name,
                    host=host,
                    port=port,
                    error=error or "unknown error",
                )


def main() -> None:
    print(
        f"[reader-health] started | poll={POLL_SECONDS}s "
        f"timeout={CONNECT_TIMEOUT_SECONDS}s "
        f"failures_before_offline={FAILURES_BEFORE_OFFLINE}"
    )

    while True:
        db: Session = SessionLocal()

        try:
            check_readers(db)
            db.commit()

        except KeyboardInterrupt:
            db.rollback()
            print("[reader-health] stopped by user")
            break

        except Exception as exc:
            db.rollback()
            print(f"[reader-health] error: {exc}")

        finally:
            db.close()

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()