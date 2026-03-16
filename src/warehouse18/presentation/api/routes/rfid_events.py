from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from warehouse18.infrastructure.db.session import get_db
from warehouse18.domain.models.rfid_event_log import RfidEventLog

router = APIRouter(prefix="/rfid", tags=["RFID Events"])


@router.get("/events/history")
def get_rfid_event_history(
    limit: int = Query(100, ge=1, le=1000),
    door_id: Optional[str] = None,
    epc: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Devuelve histórico de eventos RFID persistidos en rfid_event_log
    """

    q = db.query(RfidEventLog)

    if door_id:
        q = q.filter(RfidEventLog.door_id == door_id)

    if epc:
        q = q.filter(RfidEventLog.epc == epc)

    rows = (
        q.order_by(RfidEventLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "event_type": r.event_type,
            "reason": r.reason,
            "epc": r.epc,
            "reader_id": r.reader_id,
            "antenna": r.antenna,
            "door_id": r.door_id,
            "zone_id": r.zone_id,
            "zone_role": r.zone_role,
            "movement_code": r.movement_code,
            "movement_id": r.movement_id,
            "user_id": r.user_id,
            "mysim_user_id": r.mysim_user_id,
            "payload": r.payload_json,
            "created_at": r.created_at,
        }
        for r in rows
    ]