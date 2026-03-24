from __future__ import annotations

import os
import time
import traceback
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse18.application.integrations.mysim_sync_service import sync_movement_to_mysim
from warehouse18.infrastructure.db import SessionLocal


POLL_SECONDS = float(os.getenv("WAREHOUSE18_OUTBOX_POLL_SECONDS", "2"))
BATCH_SIZE = int(os.getenv("WAREHOUSE18_OUTBOX_BATCH_SIZE", "10"))
MAX_RETRIES = int(os.getenv("WAREHOUSE18_OUTBOX_MAX_RETRIES", "5"))
BACKOFF_SECONDS = int(os.getenv("WAREHOUSE18_OUTBOX_BACKOFF_SECONDS", "30"))


PICK_AND_MARK_PROCESSING_SQL = text(
    """
    WITH picked AS (
        SELECT id
        FROM integration_outbox
        WHERE direction = 'outbound'
          AND target_system = 'mysim'
          AND entity_type = 'movement'
          AND action = 'sync'
          AND status IN ('pending', 'error')
          AND (
                next_retry_at IS NULL
                OR next_retry_at <= now()
              )
          AND retries < :max_retries
        ORDER BY created_at ASC
        FOR UPDATE SKIP LOCKED
        LIMIT :batch_size
    )
    UPDATE integration_outbox o
    SET
        status = 'processing',
        last_attempt_at = now(),
        last_error = NULL
    FROM picked
    WHERE o.id = picked.id
    RETURNING
        o.id,
        o.entity_id,
        o.retries,
        o.payload_json,
        o.created_at
    """
)

MARK_OUTBOX_SENT_SQL = text(
    """
    UPDATE integration_outbox
    SET
        status = 'sent',
        last_attempt_at = now(),
        last_error = NULL
    WHERE id = :outbox_id
    """
)

MARK_OUTBOX_ERROR_SQL = text(
    """
    UPDATE integration_outbox
    SET
        status = 'error',
        retries = retries + 1,
        last_attempt_at = now(),
        next_retry_at = :next_retry_at,
        last_error = :last_error
    WHERE id = :outbox_id
    """
)

MARK_MOVEMENT_SYNCING_SQL = text(
    """
    UPDATE movements
    SET
        mysim_sync_status = 'syncing',
        mysim_sync_error = NULL
    WHERE id = :movement_id
      AND mysim_sync_status = 'queued'
    """
)

MARK_MOVEMENT_ERROR_SQL = text(
    """
    UPDATE movements
    SET
        mysim_sync_status = 'error',
        mysim_sync_error = :error_text
    WHERE id = :movement_id
    """
)


def claim_jobs(db: Session) -> list[dict]:
    rows = db.execute(
        PICK_AND_MARK_PROCESSING_SQL,
        {
            "batch_size": BATCH_SIZE,
            "max_retries": MAX_RETRIES,
        },
    ).mappings().all()
    db.commit()
    return [dict(r) for r in rows]


def process_one_job(outbox_row: dict) -> None:
    outbox_id = int(outbox_row["id"])
    movement_id = int(outbox_row["entity_id"])
    retries = int(outbox_row["retries"] or 0)

    db: Session = SessionLocal()
    try:
        db.execute(
            MARK_MOVEMENT_SYNCING_SQL,
            {
                "movement_id": movement_id,
            },
        )
        db.commit()

        movement = sync_movement_to_mysim(db, movement_id)

        # Si tu lógica actual ya deja movement.mysim_sync_status='ok', perfecto.
        # Aquí solo cerramos la fila del outbox.
        db.execute(
            MARK_OUTBOX_SENT_SQL,
            {
                "outbox_id": outbox_id,
            },
        )
        db.commit()

        print(
            f"[outbox] sent | outbox_id={outbox_id} movement_id={movement_id} "
            f"mysim_status={movement.mysim_sync_status} mysim_movement_id={movement.mysim_movement_id}"
        )

    except Exception as e:
        db.rollback()

        error_text = str(e)[:2000]
        next_retry_at = datetime.now(timezone.utc) + timedelta(
            seconds=BACKOFF_SECONDS * (retries + 1)
        )

        try:
            db.execute(
                MARK_MOVEMENT_ERROR_SQL,
                {
                    "movement_id": movement_id,
                    "error_text": error_text,
                },
            )
            db.execute(
                MARK_OUTBOX_ERROR_SQL,
                {
                    "outbox_id": outbox_id,
                    "next_retry_at": next_retry_at,
                    "last_error": error_text,
                },
            )
            db.commit()
        except Exception:
            db.rollback()
            print(
                f"[outbox] fatal_error_updating_state | outbox_id={outbox_id} "
                f"movement_id={movement_id}"
            )
            print(traceback.format_exc())

        print(
            f"[outbox] error | outbox_id={outbox_id} movement_id={movement_id} "
            f"retry={retries + 1}/{MAX_RETRIES} error={error_text}"
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
        db: Session = SessionLocal()
        try:
            rows = claim_jobs(db)
        except Exception:
            db.rollback()
            print("[outbox] error claiming jobs")
            print(traceback.format_exc())
            rows = []
        finally:
            db.close()

        if not rows:
            time.sleep(POLL_SECONDS)
            continue

        for row in rows:
            process_one_job(row)


if __name__ == "__main__":
    main()