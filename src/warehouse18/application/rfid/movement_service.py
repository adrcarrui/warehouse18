from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from warehouse18.application.rfid.epc96 import load_epc_schema, parse_epc96
from warehouse18.domain.models.location import Location
from warehouse18.domain.models.movement import Movement
from warehouse18.domain.models.movement_type import MovementType as LocalMovementType
from warehouse18.domain.models.user import User

log = logging.getLogger("warehouse18.rfid.movement")


# -------------------------------------------------
# EPC helpers
# -------------------------------------------------

def build_item_key_from_epc(epc: str, epc_schema_path: str) -> str:
    schema = load_epc_schema(Path(epc_schema_path))
    parsed = parse_epc96(epc, schema)

    if parsed.family_name and parsed.serial is not None:
        return f"{parsed.family_name}-{parsed.serial:06d}"

    return epc


# -------------------------------------------------
# Resolvers
# -------------------------------------------------

def resolve_local_user_by_mysim_id(db: Session, mysim_user_id: int) -> User | None:
    return db.query(User).filter(User.mysim_id == mysim_user_id).first()


def resolve_local_location_id_by_mysim_code(db: Session, external_location_id: int | str | None) -> int | None:
    if external_location_id is None:
        return None

    external_code = str(external_location_id).strip()

    loc = db.query(Location).filter(Location.code == external_code).first()
    return loc.id if loc else None

def movement_type_by_name(db: Session, name: str) -> LocalMovementType | None:
    return db.query(LocalMovementType).filter(LocalMovementType.name == name).first()


def get_movement_by_id(db: Session, movement_id: int) -> Movement | None:
    return db.query(Movement).filter(Movement.id == movement_id).first()


# -------------------------------------------------
# Create preventive movement
# -------------------------------------------------

def create_preventive_movement(
    db: Session,
    *,
    movement_type_name: str,
    epc: str,
    epc_schema_path: str,
    antenna: int,
    rssi: float | None,
    current_route: Any,
    local_user_id: int | None,
    mysim_user_id: int | None,
    from_location_id_local: int | None,
    to_location_id_local: int | None,
) -> Movement:

    mt = movement_type_by_name(db, movement_type_name)
    if mt is None:
        raise ValueError(f"movement_type_not_found_by_name:{movement_type_name}")

    item_key = build_item_key_from_epc(epc, epc_schema_path)

    notes = (
        f"RFID preventive movement | epc={epc} | "
        f"door_id={current_route.door_id} | "
        f"reader_id={current_route.reader_id} | "
        f"antenna={antenna} | "
        f"rssi={rssi} | "
        f"logical_name={current_route.logical_name} | "
        f"aisle_id={current_route.aisle_id}"
    )

    mv = Movement(
        movement_type_id=mt.id,
        item_id=None,
        quantity=Decimal("1"),
        from_location_id=from_location_id_local,
        to_location_id=to_location_id_local,
        reference_type=None,
        reference_id=None,
        user_id=local_user_id,
        notes=notes,
        item_key=item_key,
        mysim_user_id=mysim_user_id,
        review_status="pending",
        mysim_sync_status="pending_review",
        reviewed_at=None,
        reviewed_by_user_id=None,
        review_note=None,
        mysim_synced_at=None,
        mysim_sync_error=None,
        mysim_movement_id=None,
        needs_report=False,
        report_reason=None,
        is_preventive=True,
        rfid_status="pending_enrichment",
    )

    db.add(mv)
    db.commit()
    db.refresh(mv)

    return mv


# -------------------------------------------------
# Update GR
# -------------------------------------------------

def complete_receipt_destination(
    db: Session,
    *,
    movement: Movement,
    to_location_id_local: int,
    mysim_user_id: int | None = None,
) -> Movement:

    movement.to_location_id = to_location_id_local

    if mysim_user_id is not None and movement.mysim_user_id is None:
        movement.mysim_user_id = mysim_user_id
        local_user = resolve_local_user_by_mysim_id(db, mysim_user_id)
        if local_user and movement.user_id is None:
            movement.user_id = local_user.id

    movement.rfid_status = "finalized"

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement


# -------------------------------------------------
# GI -> GT
# -------------------------------------------------

def mutate_issue_to_transfer(
    db: Session,
    *,
    movement: Movement,
    to_location_id_local: int,
    mysim_user_id: int | None = None,
) -> Movement:

    mt = movement_type_by_name(db, "Goods Transfer")
    if mt is None:
        raise ValueError("movement_type_not_found_by_name:Goods Transfer")

    movement.movement_type_id = mt.id
    movement.to_location_id = to_location_id_local

    if mysim_user_id is not None and movement.mysim_user_id is None:
        movement.mysim_user_id = mysim_user_id
        local_user = resolve_local_user_by_mysim_id(db, mysim_user_id)
        if local_user and movement.user_id is None:
            movement.user_id = local_user.id

    movement.rfid_status = "finalized"

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement


# -------------------------------------------------
# Finalize preventive (timeout)
# -------------------------------------------------

def finalize_preventive_movement(
    db: Session,
    *,
    movement: Movement,
) -> Movement:

    movement.rfid_status = "finalized"

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement


# -------------------------------------------------
# Attach user later
# -------------------------------------------------

def attach_user_to_movement_if_missing(
    db: Session,
    *,
    movement: Movement,
    mysim_user_id: int,
) -> Movement:

    changed = False

    if movement.mysim_user_id is None:
        movement.mysim_user_id = mysim_user_id
        changed = True

    if movement.user_id is None:
        local_user = resolve_local_user_by_mysim_id(db, mysim_user_id)
        if local_user:
            movement.user_id = local_user.id
            changed = True

    if changed:
        db.add(movement)
        db.commit()
        db.refresh(movement)

    return movement

def update_transfer_destination(
    db: Session,
    *,
    movement,
    to_location_id_local: int | None,
    mysim_user_id: int | None = None,
):
    if to_location_id_local is not None:
        movement.to_location_id = to_location_id_local

    if mysim_user_id is not None and movement.mysim_user_id is None:
        local_user = resolve_local_user_by_mysim_id(db, mysim_user_id)
        if local_user is not None and movement.user_id is None:
            movement.user_id = local_user.id
        movement.mysim_user_id = mysim_user_id

    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement

def sync_pending_reviewed_movement(
    db: Session,
    *,
    movement,
    movement_event: Any | None = None,
):
    """
    Shim de compatibilidad para el flujo de sync a mySim.

    Objetivo inmediato:
    - restaurar el símbolo que mysim_sync_service importa
    - permitir que el worker arranque
    - no pisar datos existentes del movimiento

    Comportamiento actual:
    - refresca el movimiento desde BD
    - no modifica campos si no hay lógica de enriquecimiento definida aquí
    - devuelve el movimiento listo para que mysim_sync_service continúe

    Si más adelante quieres reintroducir enriquecimiento desde movement_event,
    se añade aquí sin tocar el worker.
    """
    try:
        db.refresh(movement)
    except Exception:
        # Si el objeto no está attached, hacemos un merge conservador
        movement = db.merge(movement)
        db.flush()

    return movement