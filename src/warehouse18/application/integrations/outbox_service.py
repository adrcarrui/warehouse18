from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


def enqueue_movement_sync(
    db: Session,
    movement_id: int,
    *,
    trigger: str = "manual_confirm",
) -> int:
    payload = {
        "movement_id": movement_id,
        "trigger": trigger,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }

    row_id = db.execute(
        text(
            """
            INSERT INTO integration_outbox (
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
                last_error
            )
            VALUES (
                'outbound',
                'mysim',
                'movement',
                :movement_id,
                'sync',
                CAST(:payload_json AS jsonb),
                'pending',
                0,
                now(),
                now(),
                NULL
            )
            RETURNING id
            """
        ),
        {
            "movement_id": movement_id,
            "payload_json": json.dumps(payload),
        },
    ).scalar_one()

    return int(row_id)