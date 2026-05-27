from __future__ import annotations

import json
import os
import time
import traceback

from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import SessionLocal


POLL_SECONDS = int(os.getenv("WAREHOUSE_MOVEMENT_ALERT_POLL_SECONDS", "10"))

PENDING_TOO_LONG_MINUTES = int(
    os.getenv("WAREHOUSE_MOVEMENT_PENDING_TOO_LONG_MINUTES", "30")
)

DONE_BY_GRACE_MINUTES = int(
    os.getenv("WAREHOUSE_MOVEMENT_DONE_BY_GRACE_MINUTES", "2")
)


def ensure_supporting_schema(db: Session) -> None:
    db.execute(
        text("""
            ALTER TABLE alerts
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
        """)
    )

    db.execute(
        text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_alert_open_by_code_movement
            ON alerts (code, movement_id)
            WHERE status = 'open'
              AND movement_id IS NOT NULL;
        """)
    )


def upsert_movement_alert(
    db: Session,
    *,
    code: str,
    title: str,
    message: str,
    severity: str,
    movement_id: int,
    item_id: int | None,
    metadata: dict,
) -> None:
    metadata_json = json.dumps(metadata, ensure_ascii=False)

    row = db.execute(
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
                movement_id,
                item_id,
                metadata,
                created_at,
                updated_at
            )
            VALUES (
                CAST(:code AS TEXT),
                CAST(:title AS TEXT),
                CAST(:message AS TEXT),
                CAST(:severity AS TEXT),
                'open',
                'movement',
                'movement',
                CAST(:entity_id AS TEXT),
                :movement_id,
                :item_id,
                CAST(:metadata AS JSONB),
                now(),
                now()
            )
            ON CONFLICT (code, movement_id)
            WHERE status = 'open'
              AND movement_id IS NOT NULL
            DO UPDATE SET
                title = EXCLUDED.title,
                message = EXCLUDED.message,
                severity = EXCLUDED.severity,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            RETURNING id, created_at, updated_at
        """),
        {
            "code": code,
            "title": title,
            "message": message,
            "severity": severity,
            "entity_id": str(movement_id),
            "movement_id": movement_id,
            "item_id": item_id,
            "metadata": metadata_json,
        },
    ).mappings().first()

    if row:
        print(
            f"[movement-alerts] alert upserted | "
            f"code={code} movement_id={movement_id} "
            f"alert_id={row['id']} created_at={row['created_at']} "
            f"updated_at={row['updated_at']}"
        )


def resolve_pending_too_long_alerts(db: Session) -> None:
    rows = db.execute(
        text("""
            UPDATE alerts a
            SET
                status = 'resolved',
                resolved_at = COALESCE(a.resolved_at, now()),
                updated_at = now()
            FROM movements m
            WHERE a.code = 'MOVEMENT_PENDING_TOO_LONG'
              AND a.status = 'open'
              AND a.movement_id = m.id
              AND COALESCE(m.review_status, 'pending') <> 'pending'
            RETURNING a.id, a.movement_id
        """)
    ).mappings().all()

    for row in rows:
        print(
            f"[movement-alerts] resolved pending-too-long | "
            f"alert_id={row['id']} movement_id={row['movement_id']}"
        )


def resolve_without_done_by_alerts(db: Session) -> None:
    rows = db.execute(
        text("""
            UPDATE alerts a
            SET
                status = 'resolved',
                resolved_at = COALESCE(a.resolved_at, now()),
                updated_at = now()
            FROM movements m
            WHERE a.code = 'MOVEMENT_WITHOUT_DONE_BY'
              AND a.status = 'open'
              AND a.movement_id = m.id
              AND (
                    m.user_id IS NOT NULL
                    OR m.mysim_user_id IS NOT NULL
              )
            RETURNING a.id, a.movement_id
        """)
    ).mappings().all()

    for row in rows:
        print(
            f"[movement-alerts] resolved without-done-by | "
            f"alert_id={row['id']} movement_id={row['movement_id']}"
        )


def create_pending_too_long_alerts(db: Session) -> None:
    rows = db.execute(
        text("""
            SELECT
                m.id AS movement_id,
                m.item_id,
                m.item_key,
                m.quantity,
                m.review_status,
                m.created_at,
                m.from_location_id,
                m.to_location_id,
                m.user_id,
                m.mysim_user_id,
                mt.code AS movement_code,
                EXTRACT(EPOCH FROM (now() - m.created_at)) / 60 AS age_minutes
            FROM movements m
            JOIN movement_types mt
                ON mt.id = m.movement_type_id
            WHERE COALESCE(m.review_status, 'pending') = 'pending'
              AND m.created_at < now() - (:pending_minutes || ' minutes')::interval
            ORDER BY m.created_at ASC
        """),
        {
            "pending_minutes": PENDING_TOO_LONG_MINUTES,
        },
    ).mappings().all()

    for row in rows:
        movement_id = int(row["movement_id"])
        movement_code = row["movement_code"] or "UNKNOWN"
        item_key = row["item_key"]
        age_minutes = int(row["age_minutes"] or 0)

        upsert_movement_alert(
            db,
            code="MOVEMENT_PENDING_TOO_LONG",
            title="Movement pending too long",
            message=(
                f"Movement #{movement_id} ({movement_code}) has been pending "
                f"for {age_minutes} minutes. Item: {item_key or 'unknown'}."
            ),
            severity="warning",
            movement_id=movement_id,
            item_id=row["item_id"],
            metadata={
                "movement_id": movement_id,
                "movement_code": movement_code,
                "item_key": item_key,
                "quantity": str(row["quantity"]) if row["quantity"] is not None else None,
                "review_status": row["review_status"],
                "created_at": (
                    row["created_at"].isoformat()
                    if row["created_at"] is not None
                    else None
                ),
                "age_minutes": age_minutes,
                "threshold_minutes": PENDING_TOO_LONG_MINUTES,
                "from_location_id": row["from_location_id"],
                "to_location_id": row["to_location_id"],
                "user_id": row["user_id"],
                "mysim_user_id": row["mysim_user_id"],
            },
        )


def create_without_done_by_alerts(db: Session) -> None:
    rows = db.execute(
        text("""
            SELECT
                m.id AS movement_id,
                m.item_id,
                m.item_key,
                m.quantity,
                m.review_status,
                m.created_at,
                m.from_location_id,
                m.to_location_id,
                m.user_id,
                m.mysim_user_id,
                mt.code AS movement_code,
                EXTRACT(EPOCH FROM (now() - m.created_at)) / 60 AS age_minutes
            FROM movements m
            JOIN movement_types mt
                ON mt.id = m.movement_type_id
            WHERE m.user_id IS NULL
              AND m.mysim_user_id IS NULL
              AND m.created_at < now() - (:grace_minutes || ' minutes')::interval
              AND COALESCE(m.review_status, 'pending') NOT IN (
                    'cancelled',
                    'canceled',
                    'rejected',
                    'void',
                    'deleted'
              )
            ORDER BY m.created_at ASC
        """),
        {
            "grace_minutes": DONE_BY_GRACE_MINUTES,
        },
    ).mappings().all()

    for row in rows:
        movement_id = int(row["movement_id"])
        movement_code = row["movement_code"] or "UNKNOWN"
        item_key = row["item_key"]

        upsert_movement_alert(
            db,
            code="MOVEMENT_WITHOUT_DONE_BY",
            title="Movement without Done By",
            message=(
                f"Movement #{movement_id} ({movement_code}) has no Done By user. "
                f"Item: {item_key or 'unknown'}."
            ),
            severity="warning",
            movement_id=movement_id,
            item_id=row["item_id"],
            metadata={
                "movement_id": movement_id,
                "movement_code": movement_code,
                "item_key": item_key,
                "quantity": str(row["quantity"]) if row["quantity"] is not None else None,
                "review_status": row["review_status"],
                "created_at": (
                    row["created_at"].isoformat()
                    if row["created_at"] is not None
                    else None
                ),
                "grace_minutes": DONE_BY_GRACE_MINUTES,
                "from_location_id": row["from_location_id"],
                "to_location_id": row["to_location_id"],
                "user_id": row["user_id"],
                "mysim_user_id": row["mysim_user_id"],
            },
        )


def run_once(db: Session) -> None:
    ensure_supporting_schema(db)

    resolve_pending_too_long_alerts(db)
    resolve_without_done_by_alerts(db)

    create_pending_too_long_alerts(db)
    create_without_done_by_alerts(db)


def main() -> None:
    print(
        f"[movement-alerts] started | poll={POLL_SECONDS}s "
        f"pending_too_long={PENDING_TOO_LONG_MINUTES}min "
        f"done_by_grace={DONE_BY_GRACE_MINUTES}min"
    )

    while True:
        db: Session = SessionLocal()

        try:
            run_once(db)
            db.commit()

        except KeyboardInterrupt:
            db.rollback()
            print("[movement-alerts] stopped by user")
            break

        except Exception as exc:
            db.rollback()
            print(f"[movement-alerts] error: {exc}")
            print(traceback.format_exc())

        finally:
            db.close()

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()