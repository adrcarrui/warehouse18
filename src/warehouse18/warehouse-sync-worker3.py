from __future__ import annotations

import os
import time
import traceback
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

# Ajusta este import si en tu proyecto SessionLocal vive en otro módulo
from warehouse18.infrastructure.db import SessionLocal

from warehouse18.application.integrations.mysim_sync_service import (
    sync_movement_to_mysim,
)


POLL_SECONDS = float(os.getenv("WAREHOUSE_OUTBOX_POLL_SECONDS", "2"))
BATCH_SIZE = int(os.getenv("WAREHOUSE_OUTBOX_BATCH_SIZE", "10"))
MAX_RETRIES = int(os.getenv("WAREHOUSE_OUTBOX_MAX_RETRIES", "5"))
BACKOFF_SECONDS = int(os.getenv("WAREHOUSE_OUTBOX_BACKOFF_SECONDS", "30"))


FETCH_PENDING_SQL = """
SELECT
    id,
    direction,
    target_system,
    entity_type,
    entity_id,
    action,
    payload_json,
    status,
    retries,
    next_retry_at,
    created_at,
    last_attempt_at,
    last_error
FROM integration_outbox
WHERE status = 'pending'
  AND COALESCE(next_retry_at, NOW()) <= NOW()
ORDER BY id
LIMIT :batch_size
"""

MARK_OUTBOX_SENT_SQL = """
UPDATE integration_outbox
SET
    status = 'sent',
    last_attempt_at = NOW(),
    last_error = NULL
WHERE id = :outbox_id
"""

MARK_OUTBOX_ERROR_SQL = """
UPDATE integration_outbox
SET
    retries = COALESCE(retries, 0) + 1,
    status = CASE
        WHEN COALESCE(retries, 0) + 1 >= :max_retries THEN 'error'
        ELSE 'pending'
    END,
    next_retry_at = CASE
        WHEN COALESCE(retries, 0) + 1 >= :max_retries THEN NULL
        ELSE :next_retry_at
    END,
    last_attempt_at = NOW(),
    last_error = :last_error
WHERE id = :outbox_id
"""

MARK_MOVEMENT_SYNCING_SQL = """
UPDATE movements
SET
    mysim_sync_status = 'syncing',
    mysim_sync_error = NULL
WHERE id = :movement_id
"""

MARK_MOVEMENT_ERROR_SQL = """
UPDATE movements
SET
    mysim_sync_status = 'error',
    mysim_sync_error = :error_text
WHERE id = :movement_id
"""


def debug_outbox(db: Session) -> None:
    print("\n================ DEBUG OUTBOX ================")

    try:
        print(f"[DEBUG] DB URL = {db.get_bind().engine.url}")
    except Exception as e:
        print(f"[DEBUG] No se pudo obtener DB URL: {e}")

    try:
        pending_count = db.execute(
            text("SELECT count(*) FROM integration_outbox WHERE status = 'pending'")
        ).scalar()
        print(f"[DEBUG] pending_count = {pending_count}")
    except Exception as e:
        print(f"[DEBUG] Error contando pending: {e}")

    try:
        rows = db.execute(
            text("""
                SELECT
                    id,
                    direction,
                    target_system,
                    entity_type,
                    entity_id,
                    action,
                    status,
                    retries,
                    next_retry_at,
                    created_at,
                    last_error
                FROM integration_outbox
                WHERE status = 'pending'
                ORDER BY id DESC
                LIMIT 10
            """)
        ).mappings().all()

        print("[DEBUG] pending_rows =")
        if not rows:
            print("    (sin filas)")
        else:
            for r in rows:
                print("   ", dict(r))
    except Exception as e:
        print(f"[DEBUG] Error listando pending_rows: {e}")

    print("==============================================\n")


def fetch_pending_jobs(db: Session, batch_size: int) -> list[dict]:
    rows = db.execute(
        text(FETCH_PENDING_SQL),
        {"batch_size": batch_size},
    ).mappings().all()

    jobs = [dict(r) for r in rows]

    print(f"[outbox] fetched_jobs={len(jobs)}")
    for job in jobs:
        print(f"[outbox] fetched_row={job}")

    return jobs


def process_one_job(outbox_row: dict) -> None:
    outbox_id = int(outbox_row["id"])
    movement_id = int(outbox_row["entity_id"])
    retries = int(outbox_row["retries"] or 0)

    print(
        f"[outbox] process_one_job | outbox_id={outbox_id} "
        f"movement_id={movement_id} retries={retries} action={outbox_row.get('action')}"
    )

    db: Session = SessionLocal()
    try:
        db.execute(
            text(MARK_MOVEMENT_SYNCING_SQL),
            {
                "movement_id": movement_id,
            },
        )
        db.commit()

        print(
            f"[outbox] movement marked syncing | outbox_id={outbox_id} "
            f"movement_id={movement_id}"
        )

        movement = sync_movement_to_mysim(db, movement_id)

        db.execute(
            text(MARK_OUTBOX_SENT_SQL),
            {
                "outbox_id": outbox_id,
            },
        )
        db.commit()

        print(
            f"[outbox] sent | outbox_id={outbox_id} movement_id={movement_id} "
            f"mysim_status={movement.mysim_sync_status} "
            f"mysim_movement_id={movement.mysim_movement_id}"
        )

    except Exception as e:
        db.rollback()

        error_text = str(e)[:2000]
        next_retry_at = datetime.now(timezone.utc) + timedelta(
            seconds=BACKOFF_SECONDS * (retries + 1)
        )

        print(
            f"[outbox] exception | outbox_id={outbox_id} movement_id={movement_id} "
            f"retry={retries + 1}/{MAX_RETRIES} error={error_text}"
        )
        print(traceback.format_exc())

        try:
            db.execute(
                text(MARK_MOVEMENT_ERROR_SQL),
                {
                    "movement_id": movement_id,
                    "error_text": error_text,
                },
            )
            db.execute(
                text(MARK_OUTBOX_ERROR_SQL),
                {
                    "outbox_id": outbox_id,
                    "next_retry_at": next_retry_at,
                    "last_error": error_text,
                    "max_retries": MAX_RETRIES,
                },
            )
            db.commit()

            print(
                f"[outbox] state updated after error | outbox_id={outbox_id} "
                f"movement_id={movement_id} next_retry_at={next_retry_at.isoformat()}"
            )
        except Exception:
            db.rollback()
            print(
                f"[outbox] fatal_error_updating_state | outbox_id={outbox_id} "
                f"movement_id={movement_id}"
            )
            print(traceback.format_exc())

    finally:
        db.close()


def main() -> None:
    print(
        f"[outbox] worker started | poll={POLL_SECONDS}s batch={BATCH_SIZE} "
        f"max_retries={MAX_RETRIES} backoff={BACKOFF_SECONDS}s"
    )

    while True:
        try:
            db: Session = SessionLocal()
            try:
                debug_outbox(db)
                jobs = fetch_pending_jobs(db, BATCH_SIZE)
            finally:
                db.close()

            if not jobs:
                time.sleep(POLL_SECONDS)
                continue

            for job in jobs:
                process_one_job(job)

        except KeyboardInterrupt:
            print("[outbox] worker stopped by user")
            break
        except Exception as e:
            print(f"[outbox] loop_error | error={e}")
            print(traceback.format_exc())
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()