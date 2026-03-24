from __future__ import annotations

from sqlalchemy.orm import Session

from warehouse18.application.rfid.movement_service import sync_pending_reviewed_movement
from warehouse18.domain.models.movement import Movement
from warehouse18.domain.models.rfid_event_log import RfidEventLog


def sync_movement_to_mysim(db: Session, movement_id: int) -> Movement:
    movement = db.query(Movement).filter(Movement.id == movement_id).first()
    if not movement:
        raise RuntimeError(f"Movement not found: {movement_id}")

    movement_event = (
        db.query(RfidEventLog)
        .filter(
            RfidEventLog.movement_id == movement_id,
            RfidEventLog.event_type == "movement_created",
        )
        .order_by(RfidEventLog.created_at.desc())
        .first()
    )
    if not movement_event:
        raise RuntimeError(f"movement_created RFID event not found for movement_id={movement_id}")

    sync_pending_reviewed_movement(
        db,
        movement=movement,
        movement_event=movement_event,
    )

    db.refresh(movement)
    return movement