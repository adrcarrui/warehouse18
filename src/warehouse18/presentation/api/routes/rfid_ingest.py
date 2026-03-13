from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from warehouse18.application.rfid.epc96 import EPCSchema, load_epc_schema, parse_epc96
from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models.app_setting import AppSetting
from warehouse18.domain.models.movement import Movement
from warehouse18.domain.models.movement_type import MovementType
from warehouse18.domain.models.user import User

log = logging.getLogger("warehouse18.rfid")

# OJO:
# main.py ya incluye este router con prefix=settings.api_prefix
# así que aquí NO pongas "/api/rfid" o acabarás con /api/api/rfid
router = APIRouter(prefix="/rfid", tags=["rfid"])

# rfid_ingest.py está en:
# src/warehouse18/presentation/api/routes/rfid_ingest.py
# parents[0] = routes
# parents[1] = api
# parents[2] = presentation
# parents[3] = warehouse18
# parents[4] = src
# parents[5] = raíz repo
REPO_ROOT = Path(__file__).resolve().parents[5]
EPC_SCHEMA_PATH = REPO_ROOT / "config" / "epc_schema.json"


class RFIDIngestIn(BaseModel):
    epc: str
    antenna: int
    rssi: Optional[float] = None


@dataclass(frozen=True)
class AntennaRoute:
    logical_name: str
    location_id: int
    zone: str
    door_id: str


ANTENNA_MAP: dict[int, AntennaRoute] = {
    1: AntennaRoute(
        logical_name="Pasillo 1",
        location_id=18,
        zone="AISLE_1",
        door_id="door_demo_1",
    ),
    2: AntennaRoute(
        logical_name="Pasillo 2",
        location_id=20,
        zone="AISLE_2",
        door_id="door_demo_1",
    ),
}

USER_PRESENCE_TTL_S = 600
USER_BIND_TTL_S = 20
USER_COOLDOWN_S = 2
CROSS_WINDOW_S = 10

_last_seen_user_by_zone: dict[tuple[str, int], float] = {}
_last_user_cooldown_by_zone: dict[tuple[str, int], float] = {}
_pending_cross_by_epc: dict[str, dict] = {}

_epc_schema: EPCSchema | None = None


def _get_schema() -> EPCSchema:
    global _epc_schema
    if _epc_schema is None:
        if not EPC_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"EPC schema not found: {EPC_SCHEMA_PATH}")
        _epc_schema = load_epc_schema(EPC_SCHEMA_PATH)
        log.info("RFID EPC schema loaded | path=%s", EPC_SCHEMA_PATH)
    return _epc_schema


def _parse_epc(epc: str) -> tuple[str, int]:
    """
    Devuelve (family_name, serial_num) usando el parser EPC96.
    """
    schema = _get_schema()
    parsed = parse_epc96(epc, schema)
    return parsed.family_name or "UNKNOWN", int(parsed.serial)


def _build_item_key(family: str, serial_num: int) -> str:
    family = str(family).strip().upper()
    return f"{family}-{serial_num:06d}"


def _rfid_create_movements_enabled(db: Session) -> bool:
    row = (
        db.query(AppSetting)
        .filter(AppSetting.key == "rfid.create_movements")
        .first()
    )
    if not row:
        return False

    value = row.value
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}

    return bool(value)


def _movement_type_by_code(db: Session, code: str) -> MovementType | None:
    return (
        db.query(MovementType)
        .filter(MovementType.code == code)
        .first()
    )


def _resolve_local_user_by_mysim_id(db: Session, mysim_user_id: int) -> User | None:
    return (
        db.query(User)
        .filter(User.mysim_id == mysim_user_id)
        .first()
    )


def _cleanup_user_presence(now_ts: float) -> None:
    expired = [
        key
        for key, ts in _last_seen_user_by_zone.items()
        if (now_ts - ts) > USER_PRESENCE_TTL_S
    ]
    for key in expired:
        _last_seen_user_by_zone.pop(key, None)


def _cleanup_pending_cross(now_ts: float) -> None:
    expired = [
        epc
        for epc, data in _pending_cross_by_epc.items()
        if (now_ts - data["ts"]) > CROSS_WINDOW_S
    ]
    for epc in expired:
        _pending_cross_by_epc.pop(epc, None)


def _find_recent_user_for_zone(zone: str, now_ts: float) -> int | None:
    """
    Busca un usuario visto recientemente en esa zona.
    Devuelve el mysim_user_id.
    """
    best_user_id: int | None = None
    best_ts = -1.0

    for (seen_zone, user_id), ts in _last_seen_user_by_zone.items():
        if seen_zone != zone:
            continue
        if (now_ts - ts) > USER_BIND_TTL_S:
            continue
        if ts > best_ts:
            best_ts = ts
            best_user_id = user_id

    return best_user_id


def _create_local_movement(
    db: Session,
    *,
    movement_code: str,
    epc: str,
    rssi: float | None,
    antenna: int,
    current_route: AntennaRoute,
    previous_route: AntennaRoute,
    local_user_id: int,
    mysim_user_id: int,
) -> tuple[bool, str]:
    mt = _movement_type_by_code(db, movement_code)
    if mt is None:
        return False, f"movement_type_not_found:{movement_code}"

    family, serial_num = _parse_epc(epc)
    item_key = _build_item_key(family, serial_num)

    notes = (
        f"RFID app history | epc={epc} | door_id={current_route.door_id} | "
        f"route={'B->A' if movement_code == 'GR' else 'A->B'} | "
        f"antenna={antenna} | rssi={rssi} | logical_name={current_route.logical_name} | "
        f"from_logical_name={previous_route.logical_name}"
    )

    mv = Movement(
        movement_type_id=mt.id,
        item_id=None,
        quantity=None,
        from_location_id=previous_route.location_id,
        to_location_id=current_route.location_id,
        reference_type=None,
        reference_id=None,
        user_id=local_user_id,
        notes=notes,
        item_key=item_key,
        mysim_user_id=mysim_user_id,
    )

    db.add(mv)
    db.commit()
    db.refresh(mv)

    log.info(
        "RFID local movement created | movement_id=%s code=%s epc=%s item_key=%s local_user_id=%s mysim_user_id=%s",
        mv.id,
        movement_code,
        epc,
        item_key,
        local_user_id,
        mysim_user_id,
    )
    return True, str(mv.id)


@router.post("/ingest")
def rfid_ingest(payload: RFIDIngestIn, db: Session = Depends(get_db)):
    now_ts = time.time()
    epc = payload.epc.strip().upper()

    log.info(
        "RFID INGEST RECEIVED | epc=%s antenna=%s rssi=%s",
        epc,
        payload.antenna,
        payload.rssi,
    )

    route = ANTENNA_MAP.get(payload.antenna)
    if route is None:
        return {
            "status": "ignored",
            "reason": "unknown_antenna",
            "epc": epc,
            "antenna": payload.antenna,
        }

    try:
        family_name, serial_num = _parse_epc(epc)
    except Exception as e:
        return {
            "status": "ignored",
            "reason": "invalid_epc",
            "detail": str(e),
            "epc": epc,
            "antenna": payload.antenna,
        }

    log.info(
        "DBG EPC FAMILY | epc=%s family=%s serial=%s antenna=%s",
        epc,
        family_name,
        serial_num,
        payload.antenna,
    )

    _cleanup_user_presence(now_ts)
    _cleanup_pending_cross(now_ts)

    # USER
    if family_name == "USER":
        mysim_user_id = serial_num
        user_key = (route.zone, mysim_user_id)

        last_seen = _last_user_cooldown_by_zone.get(user_key)
        if last_seen is not None and (now_ts - last_seen) < USER_COOLDOWN_S:
            return {
                "status": "ignored",
                "reason": "user_cooldown",
                "epc": epc,
                "antenna": payload.antenna,
                "user_id": mysim_user_id,
                "zone": route.zone,
                "seconds_since_last": now_ts - last_seen,
                "cooldown_seconds": USER_COOLDOWN_S,
            }

        _last_user_cooldown_by_zone[user_key] = now_ts
        _last_seen_user_by_zone[user_key] = now_ts

        log.info(
            "RFID USER SEEN | user_id=%s zone=%s antenna=%s rssi=%s",
            mysim_user_id,
            route.zone,
            payload.antenna,
            payload.rssi,
        )

        return {
            "status": "ok",
            "reason": "user_seen",
            "epc": epc,
            "antenna": payload.antenna,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone,
            "route_mode": "dummy_door",
            "door_id": route.door_id,
            "user_id": mysim_user_id,
            "presence_ttl_seconds": USER_PRESENCE_TTL_S,
            "bind_ttl_seconds": USER_BIND_TTL_S,
        }

    # ITEM
    prev = _pending_cross_by_epc.get(epc)

    if prev is None:
        _pending_cross_by_epc[epc] = {
            "ts": now_ts,
            "antenna": payload.antenna,
            "route": route,
        }
        return {
            "status": "ok",
            "reason": "awaiting_cross",
            "epc": epc,
            "antenna": payload.antenna,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone,
            "route_mode": "dummy_door",
            "door_id": route.door_id,
            "ref_key": epc,
        }

    prev_route: AntennaRoute = prev["route"]
    prev_antenna: int = prev["antenna"]
    prev_ts: float = prev["ts"]

    if prev_antenna == payload.antenna:
        _pending_cross_by_epc[epc] = {
            "ts": now_ts,
            "antenna": payload.antenna,
            "route": route,
        }
        return {
            "status": "ok",
            "reason": "awaiting_cross",
            "epc": epc,
            "antenna": payload.antenna,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone,
            "route_mode": "dummy_door",
            "door_id": route.door_id,
            "ref_key": epc,
        }

    delta_s = now_ts - prev_ts
    if delta_s > CROSS_WINDOW_S:
        _pending_cross_by_epc[epc] = {
            "ts": now_ts,
            "antenna": payload.antenna,
            "route": route,
        }
        return {
            "status": "ok",
            "reason": "awaiting_cross",
            "epc": epc,
            "antenna": payload.antenna,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone,
            "route_mode": "dummy_door",
            "door_id": route.door_id,
            "ref_key": epc,
        }

    if prev_antenna == 2 and payload.antenna == 1:
        movement_code = "GR"
        route_label = "B->A"
    elif prev_antenna == 1 and payload.antenna == 2:
        movement_code = "GI"
        route_label = "A->B"
    else:
        _pending_cross_by_epc.pop(epc, None)
        return {
            "status": "ignored",
            "reason": "unsupported_cross",
            "epc": epc,
            "antenna": payload.antenna,
        }

    _pending_cross_by_epc.pop(epc, None)

    mysim_user_id = _find_recent_user_for_zone(route.zone, now_ts)
    if mysim_user_id is None:
        return {
            "status": "ignored",
            "reason": "cross_detected_but_no_user",
            "epc": epc,
            "antenna": payload.antenna,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone,
            "route_mode": "dummy_door",
            "door_id": route.door_id,
            "route": route_label,
            "movement_code": movement_code,
            "ref_key": epc,
        }

    if not _rfid_create_movements_enabled(db):
        return {
            "status": "ok",
            "reason": "movement_creation_disabled",
            "epc": epc,
            "antenna": payload.antenna,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone,
            "route_mode": "dummy_door",
            "door_id": route.door_id,
            "route": route_label,
            "movement_code": movement_code,
            "user_id": mysim_user_id,
            "ref_key": epc,
        }

    local_user = _resolve_local_user_by_mysim_id(db, mysim_user_id)
    if local_user is None:
        return {
            "status": "ignored",
            "reason": "local_user_not_found_for_mysim_id",
            "epc": epc,
            "antenna": payload.antenna,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone,
            "route_mode": "dummy_door",
            "door_id": route.door_id,
            "route": route_label,
            "movement_code": movement_code,
            "user_id": mysim_user_id,
            "ref_key": epc,
        }

    log.info(
        "RFID local user resolve | mysim_user_id=%s local_user_id=%s",
        mysim_user_id,
        local_user.id,
    )

    try:
        ok, movement_id_or_reason = _create_local_movement(
            db,
            movement_code=movement_code,
            epc=epc,
            rssi=payload.rssi,
            antenna=payload.antenna,
            current_route=route,
            previous_route=prev_route,
            local_user_id=local_user.id,
            mysim_user_id=mysim_user_id,
        )
    except Exception as e:
        db.rollback()
        return {
            "status": "ignored",
            "reason": "db_integrity_error",
            "epc": epc,
            "antenna": payload.antenna,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone,
            "detail": str(e),
            "movement_code": movement_code,
            "user_id": local_user.id,
            "mysim_user_id": mysim_user_id,
        }

    if not ok:
        return {
            "status": "ignored",
            "reason": movement_id_or_reason,
            "epc": epc,
            "antenna": payload.antenna,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone,
            "movement_code": movement_code,
            "user_id": local_user.id,
            "mysim_user_id": mysim_user_id,
        }

    return {
        "status": "ok",
        "reason": "movement_created",
        "epc": epc,
        "antenna": payload.antenna,
        "logical_name": route.logical_name,
        "location_id": route.location_id,
        "zone": route.zone,
        "route_mode": "dummy_door",
        "door_id": route.door_id,
        "route": route_label,
        "movement_code": movement_code,
        "movement_id": int(movement_id_or_reason),
        "user_id": local_user.id,
        "mysim_user_id": mysim_user_id,
    }