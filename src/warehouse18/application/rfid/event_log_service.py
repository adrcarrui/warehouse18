from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from warehouse18.domain.models.rfid_event_log import RfidEventLog

log = logging.getLogger("warehouse18.rfid")


def log_rfid_event(
    db: Session,
    *,
    event_type: str,
    reason: str | None = None,
    epc: str | None = None,
    reader_id: str | None = None,
    antenna: int | None = None,
    door_id: str | None = None,
    zone_id: str | None = None,
    zone_role: str | None = None,
    movement_code: str | None = None,
    movement_id: int | None = None,
    user_id: int | None = None,
    mysim_user_id: int | None = None,
    payload_json: dict[str, Any] | None = None,
    review_status: str = "confirmed",
) -> None:
    try:
        row = RfidEventLog(
            epc=epc,
            reader_id=reader_id,
            antenna=antenna,
            door_id=door_id,
            zone_id=zone_id,
            zone_role=zone_role,
            event_type=event_type,
            reason=reason,
            movement_code=movement_code,
            movement_id=movement_id,
            user_id=user_id,
            mysim_user_id=mysim_user_id,
            payload_json=payload_json or {},
            review_status=review_status,
        )
        db.add(row)
        db.commit()
    except Exception as e:
        db.rollback()
        log.exception(
            "RFID event log insert failed | event_type=%s epc=%s movement_id=%s",
            event_type,
            epc,
            movement_id,
            e,
        )