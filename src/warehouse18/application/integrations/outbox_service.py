from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def enqueue_movement_sync(
    db: Session,
    movement_id: int,
    *,
    trigger: str = "manual_confirm",
    device_install_uninstall: dict[str, Any] | None = None,
) -> int:
    payload: dict[str, Any] = {
        "movement_id": movement_id,
        "trigger": trigger,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }

    if device_install_uninstall:
        payload["device_install_uninstall"] = {
            "unistall_part": device_install_uninstall.get("unistall_part"),
            "dest_uninstalled_part": device_install_uninstall.get("dest_uninstalled_part"),
            "uninstalled_by": device_install_uninstall.get("uninstalled_by"),
            "why_is_it_uninstalled": device_install_uninstall.get("why_is_it_uninstalled"),
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