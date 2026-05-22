from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from warehouse18.application.rfid.epc96 import (
    EPCSchema,
    format_item_key,
    load_epc_schema,
    parse_epc96,
)
from warehouse18.domain.models.location import Location
from warehouse18.domain.models.movement import Movement
from warehouse18.domain.models.movement_type import MovementType as LocalMovementType
from warehouse18.domain.models.user import User
from warehouse18.domain.models.aisle import Aisle

log = logging.getLogger("warehouse18.rfid.movement")


# -------------------------------------------------
# EPC helpers
# -------------------------------------------------

def build_item_key_from_epc(epc: str, epc_schema_path: str) -> str:
    schema: EPCSchema = load_epc_schema(epc_schema_path)
    parsed = parse_epc96(epc, schema)

    item_key = format_item_key(parsed, schema)
    if item_key is None:
        return f"UNKNOWN-{parsed.object_id:06d}"

    return item_key


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

def normalize_aisle_code(value: str | None) -> str | None:
    if not value:
        return None

    code = str(value).strip().upper()

    if not code:
        return None

    if code in ("ENTRANCE", "ENTRADA"):
        return "AISLE0"

    if code.startswith("AISLE_"):
        return "AISLE" + code.split("_", 1)[1]

    if code.startswith("PASILLO_"):
        return "AISLE" + code.split("_", 1)[1]

    return code

def resolve_tracking_mode_from_epc(epc: str, epc_schema_path: str) -> tuple[str, str | None]:
    schema: EPCSchema = load_epc_schema(epc_schema_path)
    parsed = parse_epc96(epc, schema)

    tid_hex = getattr(parsed, "tid_hex", None) or getattr(parsed, "tid", None)

    if tid_hex:
        return "serialized", str(tid_hex).upper()

    return "bulk", None

def resolve_detected_aisle_id(db: Session, current_route) -> int | None:
    aisle_code = normalize_aisle_code(getattr(current_route, "aisle_code", None))

    if not aisle_code:
        return None

    aisle = (
        db.query(Aisle)
        .filter(Aisle.code == aisle_code)
        .filter(Aisle.is_active.is_(True))
        .first()
    )

    if aisle is None:
        log.warning(
            "RFID detected aisle not found | route_aisle_code=%s normalized_code=%s antenna=%s zone=%s",
            getattr(current_route, "aisle_code", None),
            aisle_code,
            getattr(current_route, "antenna", None),
            getattr(current_route, "zone_id", None),
        )
        return None

    return int(aisle.id)

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
    
    detected_asset_code = epc.strip().upper()

    schema = load_epc_schema(epc_schema_path)
    parsed = parse_epc96(detected_asset_code, schema)

    item_key = format_item_key(parsed, schema)
    if item_key is None:
        item_key = f"UNKNOWN-{parsed.object_id:06d}"

    detected_tracking_mode = parsed.tracking_mode
    detected_tid_hex = (
        parsed.tid_serial_hex
        if parsed.tracking_mode == "serialized"
        else None
    )

    notes = (
        f"RFID preventive movement | epc={detected_asset_code} | "
        f"door_id={current_route.door_id} | "
        f"reader_id={current_route.reader_id} | "
        f"antenna={antenna} | "
        f"rssi={rssi} | "
        f"logical_name={current_route.logical_name} | "
        f"aisle_code={getattr(current_route, 'aisle_code', None)}"
    )
    detected_aisle_id = resolve_detected_aisle_id(db, current_route)

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
        detected_aisle_id=detected_aisle_id,
        detected_asset_code=detected_asset_code,
        detected_tracking_mode=detected_tracking_mode,
        detected_tid_hex=detected_tid_hex,
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