from __future__ import annotations

import logging
import os
import re
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.orm import Session
from warehouse18.domain.models import Aisle, DeviceAlias, DeviceGroup, AisleDeviceGroup
from warehouse18.application.rfid.epc96 import EPCSchema, load_epc_schema, parse_epc96
from warehouse18.application.rfid.event_log_service import log_rfid_event
from warehouse18.application.rfid.movement_service import (
    attach_user_to_movement_if_missing,
    complete_receipt_destination,
    create_preventive_movement,
    finalize_preventive_movement,
    get_movement_by_id,
    get_or_create_item_by_key,
    mutate_issue_to_transfer,
    resolve_local_location_id_by_mysim_code,
    resolve_local_user_by_mysim_id,
    update_transfer_destination,
)
from warehouse18.domain.models.app_setting import AppSetting
from warehouse18.infrastructure.config.antenna_map import (
    RouteConfig,
    load_antenna_topology,
    resolve_antenna_map_path,
)

log = logging.getLogger("warehouse18.rfid")

REPO_ROOT = Path(__file__).resolve().parents[4]
EPC_SCHEMA_PATH = REPO_ROOT / "config" / "epc_schema.json"


@dataclass
class RFIDEvent:
    epc: str
    antenna: int
    reader_id: str
    rssi: Optional[float] = None


@dataclass
class PendingMovement:
    movement_id: int
    movement_code: str  # GR | GI | GT
    created_at: float
    expires_at: float
    door_id: str
    first_route: RouteConfig
    from_location_id_local: int | None = None
    last_route: RouteConfig | None = None
    last_location_id_local: int | None = None
    receipt_destination_completed: bool = False

_epc_schema: EPCSchema | None = None
_route_index: dict[tuple[str, int], RouteConfig] | None = None

_current_user_by_door: dict[str, dict[str, Any]] = {}
_last_seen_reader_event: dict[tuple[str, int, str], float] = {}
_pending_movement_by_epc: dict[str, PendingMovement] = {}
_movement_cooldown_by_epc: dict[str, float] = {}

def close_pending_and_set_cooldown_for_review(
    *,
    movement_id: int,
    source: str,
) -> dict[str, Any]:
    _reload_runtime_config()
    now_ts = time.time()

    matched_epc = None
    matched_pending = None

    for epc_key, pending in _pending_movement_by_epc.items():
        if int(pending.movement_id) == int(movement_id):
            matched_epc = epc_key
            matched_pending = pending
            break

    if matched_epc is None or matched_pending is None:
        log.warning(
            "RFID MANUAL REVIEW CLOSE NOOP | source=%s movement_id=%s reason=no_pending_found",
            source,
            movement_id,
        )
        return {
            "closed": False,
            "reason": "no_pending_found",
            "movement_id": movement_id,
            "source": source,
        }

    _pending_movement_by_epc.pop(matched_epc, None)
    cooldown_until = now_ts + MOVE_COOLDOWN_S
    _movement_cooldown_by_epc[matched_epc] = cooldown_until

    log.warning(
        "RFID MANUAL REVIEW CLOSE APPLIED | source=%s movement_id=%s epc=%s now_ts=%.3f cooldown_until=%.3f cooldown_s=%.3f",
        source,
        movement_id,
        matched_epc,
        now_ts,
        cooldown_until,
        MOVE_COOLDOWN_S,
    )

    return {
        "closed": True,
        "reason": "pending_removed_and_cooldown_set",
        "movement_id": movement_id,
        "epc": matched_epc,
        "source": source,
        "cooldown_until": cooldown_until,
        "cooldown_seconds": MOVE_COOLDOWN_S,
    }

def _reload_runtime_config() -> None:
    global USER_PRESENCE_TTL_S
    global USER_BIND_TTL_S
    global USER_COOLDOWN_S
    global READER_DEDUPE_S
    global MOVE_COOLDOWN_S
    global PREVENTIVE_ENRICH_WINDOW_S

    USER_PRESENCE_TTL_S = int(os.getenv("WAREHOUSE18_RFID_USER_PRESENCE_TTL_SECONDS", "600"))
    USER_BIND_TTL_S = int(os.getenv("WAREHOUSE18_RFID_USER_BIND_TTL_SECONDS", "20"))
    USER_COOLDOWN_S = float(os.getenv("WAREHOUSE18_RFID_USER_COOLDOWN_SECONDS", "2"))
    READER_DEDUPE_S = float(os.getenv("WAREHOUSE18_RFID_READER_DEDUPE_SECONDS", "0.6"))
    MOVE_COOLDOWN_S = float(os.getenv("WAREHOUSE18_RFID_MOVE_COOLDOWN_SECONDS", "0"))
    PREVENTIVE_ENRICH_WINDOW_S = float(
        os.getenv("WAREHOUSE18_RFID_PREVENTIVE_ENRICH_WINDOW_SECONDS", "30")
    )

    log.warning(
        "RFID CONFIG RELOADED | PREVENTIVE_ENRICH_WINDOW_S=%s MOVE_COOLDOWN_S=%s USER_BIND_TTL_S=%s",
        PREVENTIVE_ENRICH_WINDOW_S,
        MOVE_COOLDOWN_S,
        USER_BIND_TTL_S,
    )


def _get_schema() -> EPCSchema:
    global _epc_schema
    if _epc_schema is None:
        if not EPC_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"EPC schema not found: {EPC_SCHEMA_PATH}")
        _epc_schema = load_epc_schema(EPC_SCHEMA_PATH)
        log.info("RFID EPC schema loaded | path=%s", EPC_SCHEMA_PATH)
    return _epc_schema


def _get_route_index() -> dict[tuple[str, int], RouteConfig]:
    global _route_index
    if _route_index is None:
        topology = load_antenna_topology(resolve_antenna_map_path())
        _route_index = topology.routes
        log.info("RFID topology loaded | routes=%s", len(_route_index))
    return _route_index


def _resolve_route(reader_id: str, antenna: int) -> RouteConfig | None:
    return _get_route_index().get((reader_id, antenna))


def _parse_epc(epc: str) -> tuple[str, int]:
    schema = _get_schema()
    parsed = parse_epc96(epc, schema)
    return parsed.family_name or "UNKNOWN", int(parsed.serial)


def _rfid_create_movements_enabled(db: Session) -> bool:
    row = db.query(AppSetting).filter(AppSetting.key == "rfid.create_movements").first()
    if not row:
        return False

    value = row.value
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _cleanup_user_bindings(now_ts: float) -> None:
    expired = [
        door_id
        for door_id, data in _current_user_by_door.items()
        if (now_ts - float(data["ts"])) > USER_PRESENCE_TTL_S
    ]
    for door_id in expired:
        _current_user_by_door.pop(door_id, None)


def _cleanup_reader_dedupe(now_ts: float) -> None:
    expired = [
        key
        for key, ts in _last_seen_reader_event.items()
        if (now_ts - ts) > READER_DEDUPE_S
    ]
    for key in expired:
        _last_seen_reader_event.pop(key, None)


def _cleanup_movement_cooldowns(now_ts: float) -> None:
    expired = [epc for epc, ts in _movement_cooldown_by_epc.items() if now_ts >= ts]
    for epc in expired:
        _movement_cooldown_by_epc.pop(epc, None)


def _find_recent_user_for_door(door_id: str, now_ts: float) -> int | None:
    data = _current_user_by_door.get(door_id)
    if not data:
        return None
    if (now_ts - float(data["ts"])) > USER_BIND_TTL_S:
        return None
    return int(data["user_id"])

def _refresh_pending_window(
    pending: PendingMovement,
    *,
    now_ts: float,
) -> None:
    pending.expires_at = now_ts + PREVENTIVE_ENRICH_WINDOW_S

def _is_entrance(route: RouteConfig) -> bool:
    return route.aisle_id == "ENTRANCE"


def _is_aisle(route: RouteConfig) -> bool:
    return _route_storage_aisle_code(route) is not None

def _normalize_storage_aisle_code(value: str | None) -> str | None:
    if not value:
        return None

    text_value = str(value).strip().upper()

    compact = (
        text_value
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
    )

    if compact in {"ENTRANCE", "ENTRADA", "AISLE0", "W18AISLE0"}:
        return None

    # AISLE_1_B, AISLE1, W18_AISLE_2, W18AISLE2
    match = re.search(r"(?:W18)?[_\s-]*AISLE[_\s-]*(\d+)", text_value)
    if match:
        return f"AISLE{int(match.group(1))}"

    # PASILLO_1, PASILLO 2, Pasillo 1 antena 2
    match = re.search(r"PASILLO[_\s-]*(\d+)", text_value)
    if match:
        return f"AISLE{int(match.group(1))}"

    return None

def _route_storage_aisle_code(route: RouteConfig) -> str | None:
    """
    Devuelve AISLE{N} si la ruta corresponde a un pasillo real
    de almacenamiento.

    Prioriza zone_id porque representa mejor la antena física detectada.
    AISLE0 / ENTRANCE no debe considerarse pasillo de destino.
    """
    log.warning(
        "RFID ROUTE AISLE RAW | antenna=%s aisle_id=%s location_id=%s zone_id=%s logical_name=%s",
        getattr(route, "antenna", None),
        getattr(route, "aisle_id", None),
        getattr(route, "location_id", None),
        getattr(route, "zone_id", None),
        getattr(route, "logical_name", None),
    )

    for value in (
        route.zone_id,
        route.logical_name,
        route.location_id,
        route.aisle_id,
    ):
        aisle_code = _normalize_storage_aisle_code(value)
        if aisle_code:
            log.warning(
                "RFID ROUTE AISLE RESOLVED | antenna=%s raw_value=%s resolved=%s",
                getattr(route, "antenna", None),
                value,
                aisle_code,
            )
            return aisle_code

    log.warning(
        "RFID ROUTE AISLE NOT RESOLVED | antenna=%s zone_id=%s logical_name=%s location_id=%s aisle_id=%s",
        getattr(route, "antenna", None),
        getattr(route, "zone_id", None),
        getattr(route, "logical_name", None),
        getattr(route, "location_id", None),
        getattr(route, "aisle_id", None),
    )

    return None

def _get_active_aisle_by_code(db: Session, aisle_code: str) -> Aisle | None:
    return (
        db.query(Aisle)
        .filter(Aisle.code == aisle_code)
        .filter(Aisle.is_active.is_(True))
        .first()
    )

def _ensure_item_and_origin_from_state(
    db: Session,
    *,
    movement,
    movement_code: str | None,
):
    """
    Asegura que el movimiento queda enlazado al item local y,
    para GI/GT, carga el origen real desde items.current_location_id
    si todavía está vacío.
    """
    if not getattr(movement, "item_key", None):
        return movement

    item = get_or_create_item_by_key(db, movement.item_key)

    changed = False

    if movement.item_id is None:
        movement.item_id = item.id
        changed = True

    if movement_code in {"GI", "GT"} and movement.from_location_id is None:
        movement.from_location_id = item.current_location_id
        changed = True

    if changed:
        db.add(movement)
        db.commit()
        db.refresh(movement)

    return movement

def _device_group_codes_for_item_key(db: Session, item_key: str | None) -> list[str]:
    if not item_key:
        return []

    prefix = item_key.split("-", 1)[0].strip().upper()

    if not prefix:
        return []

    codes = {prefix}

    row = (
        db.query(DeviceAlias, DeviceGroup)
        .join(DeviceGroup, DeviceGroup.id == DeviceAlias.device_group_id)
        .filter(DeviceAlias.alias_code == prefix)
        .filter(DeviceAlias.is_active.is_(True))
        .filter(DeviceGroup.is_active.is_(True))
        .first()
    )

    if row:
        _, device_group = row
        codes.add(str(device_group.code).strip().upper())

    # Refuerzo explícito para tus equivalencias actuales
    if prefix in {"295", "C295"}:
        codes.update({"295", "C295"})

    if prefix in {"235", "CN235"}:
        codes.update({"235", "CN235"})

    return sorted(codes)


def _aisle_allows_item_key(
    db: Session,
    *,
    aisle_id: int,
    item_key: str | None,
) -> bool:
    device_group_codes = _device_group_codes_for_item_key(db, item_key)

    if not device_group_codes:
        return False

    return (
        db.query(AisleDeviceGroup)
        .join(DeviceGroup, DeviceGroup.id == AisleDeviceGroup.device_group_id)
        .filter(AisleDeviceGroup.aisle_id == aisle_id)
        .filter(AisleDeviceGroup.is_active.is_(True))
        .filter(DeviceGroup.is_active.is_(True))
        .filter(DeviceGroup.code.in_(device_group_codes))
        .first()
        is not None
    )

def _set_gi_ready_for_origin_selection_from_route(
    db: Session,
    *,
    movement,
    route: RouteConfig,
    mysim_user_id: int | None,
):
    aisle_code = _route_storage_aisle_code(route)

    if aisle_code:
        aisle = _get_active_aisle_by_code(db, aisle_code)
        if aisle is not None:
            movement.detected_aisle_id = aisle.id

    if mysim_user_id is not None:
        movement = attach_user_to_movement_if_missing(
            db,
            movement=movement,
            mysim_user_id=mysim_user_id,
        )

    # GI: el origen real debe venir del estado actual del item.
    # No usamos la localización técnica del pasillo como origen.
    movement = _ensure_item_and_origin_from_state(
        db,
        movement=movement,
        movement_code="GI",
    )

    movement.to_location_id = None
    movement.rfid_status = "ready_for_location"

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement, aisle_code

def _set_ready_for_location_from_route(
    db: Session,
    *,
    movement,
    route: RouteConfig,
    mysim_user_id: int | None,
):
    aisle_code = _route_storage_aisle_code(route)

    if not aisle_code:
        movement.rfid_status = "waiting_storage_aisle"
        db.add(movement)
        db.commit()
        db.refresh(movement)
        return movement, None, False

    aisle = _get_active_aisle_by_code(db, aisle_code)

    if aisle is None:
        movement.rfid_status = "wrong_aisle"
        movement.to_location_id = None
        db.add(movement)
        db.commit()
        db.refresh(movement)
        return movement, aisle_code, False

    if mysim_user_id is not None:
        movement = attach_user_to_movement_if_missing(
            db,
            movement=movement,
            mysim_user_id=mysim_user_id,
        )

    allowed = _aisle_allows_item_key(
        db,
        aisle_id=aisle.id,
        item_key=movement.item_key,
    )

    movement.detected_aisle_id = aisle.id
    movement.to_location_id = None
    movement.rfid_status = "ready_for_location" if allowed else "wrong_aisle"

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement, aisle_code, allowed

def _try_attach_recent_user_to_latest_pending_movement_for_door(
    *,
    db: Session,
    door_id: str,
    mysim_user_id: int,
    now_ts: float,
) -> dict[str, Any] | None:
    candidates = [
        (epc, pending)
        for epc, pending in _pending_movement_by_epc.items()
        if pending.door_id == door_id and now_ts <= pending.expires_at
    ]

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[1].created_at, reverse=True)
    epc, pending = candidates[0]

    movement = get_movement_by_id(db, pending.movement_id)
    if movement is None:
        return None

    before_user_id = movement.user_id
    before_mysim_user_id = movement.mysim_user_id

    movement = attach_user_to_movement_if_missing(
        db,
        movement=movement,
        mysim_user_id=mysim_user_id,
    )

    if movement.user_id == before_user_id and movement.mysim_user_id == before_mysim_user_id:
        return None

    log_rfid_event(
        db,
        event_type="pending_movement_user_attached",
        reason="late_user_attached_to_pending_movement",
        epc=epc,
        reader_id=pending.first_route.reader_id,
        antenna=pending.first_route.antenna,
        door_id=pending.door_id,
        zone_id=pending.first_route.zone_id,
        zone_role=pending.first_route.zone_role,
        movement_code=pending.movement_code,
        payload_json={
            "movement_id": movement.id,
            "user_id": movement.user_id,
            "mysim_user_id": movement.mysim_user_id,
            "review_status": movement.review_status,
            "lag_seconds": round(now_ts - pending.created_at, 3),
        },
    )

    return {
        "status": "ok",
        "reason": "late_user_attached_to_pending_movement",
        "movement_id": movement.id,
        "movement_code": pending.movement_code,
        "user_id": movement.user_id,
        "mysim_user_id": movement.mysim_user_id,
        "epc": epc,
    }


def _cleanup_expired_pending_movements(db: Session, now_ts: float) -> None:
    expired = [
        (epc, pending)
        for epc, pending in _pending_movement_by_epc.items()
        if now_ts > pending.expires_at
    ]

    for epc, pending in expired:
        _pending_movement_by_epc.pop(epc, None)

        movement = get_movement_by_id(db, pending.movement_id)
        if movement is None:
            continue

        try:
            finalize_preventive_movement(db, movement=movement)
            _movement_cooldown_by_epc[epc] = now_ts + MOVE_COOLDOWN_S

            log.info(
                "RFID preventive movement finalized by timeout | epc=%s movement_id=%s movement_code=%s",
                epc,
                movement.id,
                pending.movement_code,
            )

            log_rfid_event(
                db,
                event_type="preventive_movement_expired",
                reason="preventive_enrichment_window_expired",
                epc=epc,
                reader_id=pending.first_route.reader_id,
                antenna=pending.first_route.antenna,
                door_id=pending.door_id,
                zone_id=pending.first_route.zone_id,
                zone_role=pending.first_route.zone_role,
                movement_code=pending.movement_code,
                payload_json={
                    "movement_id": movement.id,
                    "user_id": movement.user_id,
                    "mysim_user_id": movement.mysim_user_id,
                    "review_status": movement.review_status,
                    "window_seconds": PREVENTIVE_ENRICH_WINDOW_S,
                },
            )
        except Exception as e:
            db.rollback()
            log.exception(
                "RFID preventive movement timeout finalize failed | epc=%s movement_id=%s error=%s",
                epc,
                pending.movement_id,
                e,
            )


def process_event(db: Session, event: RFIDEvent) -> dict[str, Any]:
    _reload_runtime_config()

    now_ts = time.time()
    epc = event.epc.strip().upper()
    reader_id = event.reader_id.strip() or "reader-1"

    _cleanup_user_bindings(now_ts)
    _cleanup_reader_dedupe(now_ts)
    _cleanup_movement_cooldowns(now_ts)
    _cleanup_expired_pending_movements(db, now_ts)

    route = _resolve_route(reader_id, event.antenna)
    if route is None:
        log_rfid_event(
            db,
            event_type="unknown_reader_or_antenna",
            reason="unknown_reader_or_antenna",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
        )
        return {
            "status": "ignored",
            "reason": "unknown_reader_or_antenna",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
        }

    if not route.enabled:
        log_rfid_event(
            db,
            event_type="route_disabled",
            reason="route_disabled",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
        )
        return {
            "status": "ignored",
            "reason": "route_disabled",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "door_id": route.door_id,
            "zone": route.zone_id,
        }

    try:
        family_name, serial_num = _parse_epc(epc)
    except Exception as e:
        log.info(
            "RFID EPC rejected | epc=%s reader_id=%s antenna=%s reason=invalid_epc detail=%s",
            epc,
            reader_id,
            event.antenna,
            e,
        )
        log_rfid_event(
            db,
            event_type="epc_rejected",
            reason="invalid_epc",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            payload_json={"detail": str(e)},
        )
        return {
            "status": "ignored",
            "reason": "invalid_epc",
            "detail": str(e),
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
        }

    if family_name == "USER":
        existing = _current_user_by_door.get(route.door_id)
        if (
            existing
            and int(existing["user_id"]) == serial_num
            and (now_ts - float(existing["ts"])) < USER_COOLDOWN_S
        ):
            log_rfid_event(
                db,
                event_type="user_cooldown",
                reason="user_cooldown",
                epc=epc,
                reader_id=reader_id,
                antenna=event.antenna,
                door_id=route.door_id,
                zone_id=route.zone_id,
                zone_role=route.zone_role,
                payload_json={"mysim_user_id": serial_num},
            )
            return {
                "status": "ignored",
                "reason": "user_cooldown",
                "epc": epc,
                "antenna": event.antenna,
                "reader_id": reader_id,
                "door_id": route.door_id,
                "zone": route.zone_id,
                "zone_role": route.zone_role,
                "user_id": serial_num,
            }

        _current_user_by_door[route.door_id] = {
            "user_id": serial_num,
            "ts": now_ts,
            "zone_id": route.zone_id,
            "zone_role": route.zone_role,
            "reader_id": route.reader_id,
        }

        attached = _try_attach_recent_user_to_latest_pending_movement_for_door(
            db=db,
            door_id=route.door_id,
            mysim_user_id=serial_num,
            now_ts=now_ts,
        )

        log_rfid_event(
            db,
            event_type="user_seen",
            reason="user_seen",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            payload_json={
                "mysim_user_id": serial_num,
                "logical_name": route.logical_name,
                "location_id": route.location_id,
                "presence_ttl_seconds": USER_PRESENCE_TTL_S,
                "bind_ttl_seconds": USER_BIND_TTL_S,
            },
        )

        if attached is not None:
            attached["presence_ttl_seconds"] = USER_PRESENCE_TTL_S
            attached["bind_ttl_seconds"] = USER_BIND_TTL_S
            attached["door_id"] = route.door_id
            attached["zone"] = route.zone_id
            attached["zone_role"] = route.zone_role
            return attached

        return {
            "status": "ok",
            "reason": "user_seen",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
            "route_mode": "door_engine",
            "door_id": route.door_id,
            "user_id": serial_num,
            "presence_ttl_seconds": USER_PRESENCE_TTL_S,
            "bind_ttl_seconds": USER_BIND_TTL_S,
        }

    dedupe_key = (reader_id, event.antenna, epc)
    last_seen = _last_seen_reader_event.get(dedupe_key)
    if last_seen is not None and (now_ts - last_seen) < READER_DEDUPE_S:
        log_rfid_event(
            db,
            event_type="duplicate_reader_event",
            reason="duplicate_reader_event",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
        )
        return {
            "status": "ignored",
            "reason": "duplicate_reader_event",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "door_id": route.door_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
        }

    _last_seen_reader_event[dedupe_key] = now_ts

    if route.zone_role not in {"A", "B"}:
        log_rfid_event(
            db,
            event_type="non_passage_zone",
            reason="non_passage_zone",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
        )
        return {
            "status": "ignored",
            "reason": "non_passage_zone",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "door_id": route.door_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
        }

    cooldown_until = _movement_cooldown_by_epc.get(epc)
    if cooldown_until is not None and now_ts < cooldown_until:
        log_rfid_event(
            db,
            event_type="movement_cooldown",
            reason="movement_cooldown",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            payload_json={"cooldown_remaining": round(cooldown_until - now_ts, 3)},
        )
        return {
            "status": "ignored",
            "reason": "movement_cooldown",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "door_id": route.door_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
            "cooldown_remaining": round(cooldown_until - now_ts, 3),
        }

    if not _rfid_create_movements_enabled(db):
        log_rfid_event(
            db,
            event_type="movement_creation_disabled",
            reason="movement_creation_disabled",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
        )
        return {
            "status": "ok",
            "reason": "movement_creation_disabled",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
            "route_mode": "door_engine",
            "door_id": route.door_id,
            "ref_key": f"{route.door_id}:{epc}",
        }

    pending = _pending_movement_by_epc.get(epc)
    recent_mysim_user_id = _find_recent_user_for_door(route.door_id, now_ts)
    local_user = (
        resolve_local_user_by_mysim_id(db, recent_mysim_user_id)
        if recent_mysim_user_id is not None
        else None
    )

    # Primera lectura en entrada -> GR preventivo
    if pending is None and _is_entrance(route):
        movement = create_preventive_movement(
            db,
            movement_type_name="Goods Receipt",
            epc=epc,
            epc_schema_path=str(EPC_SCHEMA_PATH),
            antenna=event.antenna,
            rssi=event.rssi,
            current_route=route,
            local_user_id=local_user.id if local_user else None,
            mysim_user_id=recent_mysim_user_id,
            from_location_id_local=None,
            to_location_id_local=None,
        )

        pending = PendingMovement(
            movement_id=int(movement.id),
            movement_code="GR",
            created_at=now_ts,
            expires_at=now_ts + PREVENTIVE_ENRICH_WINDOW_S,
            door_id=route.door_id,
            first_route=route,
            from_location_id_local=None,
            last_route=route,
            last_location_id_local=None,
            receipt_destination_completed=False,
        )
        _pending_movement_by_epc[epc] = pending

        log_rfid_event(
            db,
            event_type="movement_created",
            reason="preventive_gr_created",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            movement_code="GR",
            payload_json={
                "movement_id": movement.id,
                "item_key": movement.item_key,
                "route": route.aisle_id,
                "window_seconds": PREVENTIVE_ENRICH_WINDOW_S,
                "rfid_status": movement.rfid_status,
                "review_status": movement.review_status,
                "user_id": movement.user_id,
                "mysim_user_id": movement.mysim_user_id,
            },
        )

        return {
            "status": "ok",
            "reason": "preventive_gr_created",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
            "route_mode": "door_engine",
            "door_id": route.door_id,
            "movement_id": movement.id,
            "movement_code": "GR",
            "review_status": movement.review_status,
            "rfid_status": movement.rfid_status,
            "ref_key": f"{route.door_id}:{epc}",
        }

    # Primera lectura en pasillo -> GI preventivo
    if pending is None and _is_aisle(route):
        technical_from_location_id_local = resolve_local_location_id_by_mysim_code(
            db,
            route.location_id,
        )

        movement = create_preventive_movement(
            db,
            movement_type_name="Goods Issue",
            epc=epc,
            epc_schema_path=str(EPC_SCHEMA_PATH),
            antenna=event.antenna,
            rssi=event.rssi,
            current_route=route,
            local_user_id=local_user.id if local_user else None,
            mysim_user_id=recent_mysim_user_id,

            # Importante:
            # No queremos guardar w18-aisle1 / w18-aisle2 como origen real.
            from_location_id_local=None,
            to_location_id_local=None,
        )

        movement, storage_aisle_code = _set_gi_ready_for_origin_selection_from_route(
            db,
            movement=movement,
            route=route,
            mysim_user_id=recent_mysim_user_id,
        )

        pending = PendingMovement(
            movement_id=int(movement.id),
            movement_code="GI",
            created_at=now_ts,
            expires_at=now_ts + PREVENTIVE_ENRICH_WINDOW_S,
            door_id=route.door_id,
            first_route=route,

            # Esto solo sirve internamente para saber desde qué zona técnica empezó.
            # No es el from_location_id real del movimiento.
            from_location_id_local=technical_from_location_id_local,

            last_route=route,
            last_location_id_local=technical_from_location_id_local,
            receipt_destination_completed=False,
        )
        _pending_movement_by_epc[epc] = pending

        log_rfid_event(
            db,
            event_type="movement_created",
            reason="preventive_gi_created",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            movement_code="GI",
            payload_json={
                "movement_id": movement.id,
                "item_key": movement.item_key,
                "route": route.aisle_id,
                "window_seconds": PREVENTIVE_ENRICH_WINDOW_S,
                "rfid_status": movement.rfid_status,
                "review_status": movement.review_status,
                "user_id": movement.user_id,
                "mysim_user_id": movement.mysim_user_id,
                "from_location_id_local": technical_from_location_id_local,
                "detected_aisle_id": movement.detected_aisle_id,
                "detected_aisle_code": storage_aisle_code,
            },
        )

        return {
            "status": "ok",
            "reason": "preventive_gi_created",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
            "route_mode": "door_engine",
            "door_id": route.door_id,
            "movement_id": movement.id,
            "movement_code": "GI",
            "review_status": movement.review_status,
            "rfid_status": movement.rfid_status,
            "detected_aisle_id": movement.detected_aisle_id,
            "detected_aisle_code": storage_aisle_code,
            "from_location_id": movement.from_location_id,
            "to_location_id": movement.to_location_id,
            "ref_key": f"{route.door_id}:{epc}",
        }

    if pending is None:
        return {
            "status": "ignored",
            "reason": "no_preventive_rule_matched",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "door_id": route.door_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
        }

    movement = get_movement_by_id(db, pending.movement_id)
    if movement is None:
        _pending_movement_by_epc.pop(epc, None)
        return {
            "status": "ignored",
            "reason": "pending_movement_not_found",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "door_id": route.door_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
        }
    
    movement = _ensure_item_and_origin_from_state(
    db,
    movement=movement,
    movement_code=pending.movement_code,
    )

    # GR preventivo: se crea en entrada y permanece abierto hasta timeout o confirm/reject
    if pending.movement_code == "GR":
        _refresh_pending_window(pending, now_ts=now_ts)
        pending.last_route = route

        if _is_entrance(route):
            return {
                "status": "ok",
                "reason": "preventive_gr_waiting_destination",
                "epc": epc,
                "antenna": event.antenna,
                "reader_id": reader_id,
                "door_id": route.door_id,
                "zone": route.zone_id,
                "zone_role": route.zone_role,
                "movement_id": movement.id,
                "movement_code": "GR",
                "receipt_destination_completed": pending.receipt_destination_completed,
            }

        if _is_aisle(route):
            _refresh_pending_window(pending, now_ts=now_ts)
            pending.last_route = route
            pending.last_location_id_local = None

            movement, storage_aisle_code, allowed = _set_ready_for_location_from_route(
                db,
                movement=movement,
                route=route,
                mysim_user_id=recent_mysim_user_id,
            )

            log_rfid_event(
                db,
                event_type="movement_updated",
                reason=(
                    "preventive_gr_ready_for_location"
                    if allowed
                    else "preventive_gr_wrong_aisle"
                ),
                epc=epc,
                reader_id=reader_id,
                antenna=event.antenna,
                door_id=route.door_id,
                zone_id=route.zone_id,
                zone_role=route.zone_role,
                movement_code="GR",
                payload_json={
                    "movement_id": movement.id,
                    "item_key": movement.item_key,
                    "route_aisle_id": route.aisle_id,
                    "storage_aisle_code": storage_aisle_code,
                    "detected_aisle_id": movement.detected_aisle_id,
                    "to_location_id": movement.to_location_id,
                    "rfid_status": movement.rfid_status,
                    "review_status": movement.review_status,
                    "user_id": movement.user_id,
                    "mysim_user_id": movement.mysim_user_id,
                    "allowed": allowed,
                    "expires_at": pending.expires_at,
                },
            )

            return {
                "status": "ok",
                "reason": (
                    "preventive_gr_ready_for_location"
                    if allowed
                    else "preventive_gr_wrong_aisle"
                ),
                "epc": epc,
                "antenna": event.antenna,
                "reader_id": reader_id,
                "logical_name": route.logical_name,
                "location_id": route.location_id,
                "zone": route.zone_id,
                "zone_role": route.zone_role,
                "route_mode": "door_engine",
                "door_id": route.door_id,
                "movement_id": movement.id,
                "movement_code": "GR",
                "review_status": movement.review_status,
                "rfid_status": movement.rfid_status,
                "detected_aisle_id": movement.detected_aisle_id,
                "detected_aisle_code": storage_aisle_code,
                "to_location_id": movement.to_location_id,
                "allowed": allowed,
                "receipt_destination_completed": False,
                "ref_key": f"{route.door_id}:{epc}",
            }

    # GI preventivo + lectura en otro pasillo -> mutar a GT
    if pending.movement_code == "GI":
        if _is_aisle(route):
            to_location_id_local = resolve_local_location_id_by_mysim_code(db, route.location_id)

            _refresh_pending_window(pending, now_ts=now_ts)
            pending.last_route = route
            pending.last_location_id_local = to_location_id_local

            first_storage_aisle_code = _route_storage_aisle_code(pending.first_route)
            current_storage_aisle_code = _route_storage_aisle_code(route)

            log.warning(
                "RFID GI AISLE COMPARE | movement_id=%s item_key=%s first_storage_aisle=%s current_storage_aisle=%s pending_from_location_id_local=%s current_location_id_local=%s route_location_id=%s route_zone=%s route_logical_name=%s",
                movement.id,
                movement.item_key,
                first_storage_aisle_code,
                current_storage_aisle_code,
                pending.from_location_id_local,
                to_location_id_local,
                route.location_id,
                route.zone_id,
                route.logical_name,
            )

            if (
                first_storage_aisle_code is not None
                and current_storage_aisle_code is not None
                and first_storage_aisle_code == current_storage_aisle_code
            ):
                movement, storage_aisle_code = _set_gi_ready_for_origin_selection_from_route(
                    db,
                    movement=movement,
                    route=route,
                    mysim_user_id=recent_mysim_user_id,
                )

                return {
                    "status": "ok",
                    "reason": "preventive_gi_same_aisle",
                    "epc": epc,
                    "antenna": event.antenna,
                    "reader_id": reader_id,
                    "door_id": route.door_id,
                    "zone": route.zone_id,
                    "zone_role": route.zone_role,
                    "movement_id": movement.id,
                    "movement_code": "GI",
                    "first_storage_aisle": first_storage_aisle_code,
                    "current_storage_aisle": current_storage_aisle_code,
                    "detected_aisle_id": movement.detected_aisle_id,
                    "detected_aisle_code": storage_aisle_code,
                }
            movement = mutate_issue_to_transfer(
                db,
                movement=movement,
                to_location_id_local=to_location_id_local,
                mysim_user_id=recent_mysim_user_id,
            )

            movement, storage_aisle_code, allowed = _set_ready_for_location_from_route(
                db,
                movement=movement,
                route=route,
                mysim_user_id=recent_mysim_user_id,
            )

            pending.movement_code = "GT"
            pending.last_route = route
            pending.last_location_id_local = None

            log_rfid_event(
                db,
                event_type="movement_updated",
                reason=(
                    "preventive_gi_mutated_to_gt_ready_for_location"
                    if allowed
                    else "preventive_gi_mutated_to_gt_wrong_aisle"
                ),
                epc=epc,
                reader_id=reader_id,
                antenna=event.antenna,
                door_id=route.door_id,
                zone_id=route.zone_id,
                zone_role=route.zone_role,
                movement_code="GT",
                payload_json={
                    "movement_id": movement.id,
                    "item_key": movement.item_key,
                    "route": f"{pending.first_route.aisle_id}->{route.aisle_id}",
                    "from_location_id_local": pending.from_location_id_local,
                    "storage_aisle_code": storage_aisle_code,
                    "detected_aisle_id": movement.detected_aisle_id,
                    "to_location_id": movement.to_location_id,
                    "last_seen_aisle": route.aisle_id,
                    "expires_at": pending.expires_at,
                    "rfid_status": movement.rfid_status,
                    "review_status": movement.review_status,
                    "user_id": movement.user_id,
                    "mysim_user_id": movement.mysim_user_id,
                    "allowed": allowed,
                },
            )

            return {
                "status": "ok",
                "reason": (
                    "preventive_gi_mutated_to_gt_ready_for_location"
                    if allowed
                    else "preventive_gi_mutated_to_gt_wrong_aisle"
                ),
                "epc": epc,
                "antenna": event.antenna,
                "reader_id": reader_id,
                "logical_name": route.logical_name,
                "location_id": route.location_id,
                "zone": route.zone_id,
                "zone_role": route.zone_role,
                "route_mode": "door_engine",
                "door_id": route.door_id,
                "movement_id": movement.id,
                "movement_code": "GT",
                "review_status": movement.review_status,
                "rfid_status": movement.rfid_status,
                "detected_aisle_id": movement.detected_aisle_id,
                "detected_aisle_code": storage_aisle_code,
                "to_location_id": movement.to_location_id,
                "allowed": allowed,
                "ref_key": f"{route.door_id}:{epc}",
            }

        if _is_entrance(route):
            _refresh_pending_window(pending, now_ts=now_ts)
            pending.last_route = route

            return {
                "status": "ok",
                "reason": "preventive_gi_waiting_confirmation_or_other_aisle",
                "epc": epc,
                "antenna": event.antenna,
                "reader_id": reader_id,
                "door_id": route.door_id,
                "zone": route.zone_id,
                "zone_role": route.zone_role,
                "movement_id": movement.id,
                "movement_code": "GI",
            }

    if pending.movement_code == "GT":
        _refresh_pending_window(pending, now_ts=now_ts)

        if _is_aisle(route):
            pending.last_route = route
            pending.last_location_id_local = None

            movement, storage_aisle_code, allowed = _set_ready_for_location_from_route(
                db,
                movement=movement,
                route=route,
                mysim_user_id=recent_mysim_user_id,
            )

            log_rfid_event(
                db,
                event_type="movement_updated",
                reason=(
                    "pending_gt_ready_for_location"
                    if allowed
                    else "pending_gt_wrong_aisle"
                ),
                epc=epc,
                reader_id=reader_id,
                antenna=event.antenna,
                door_id=route.door_id,
                zone_id=route.zone_id,
                zone_role=route.zone_role,
                movement_code="GT",
                payload_json={
                    "movement_id": movement.id,
                    "item_key": movement.item_key,
                    "route_aisle_id": route.aisle_id,
                    "storage_aisle_code": storage_aisle_code,
                    "detected_aisle_id": movement.detected_aisle_id,
                    "to_location_id": movement.to_location_id,
                    "expires_at": pending.expires_at,
                    "review_status": movement.review_status,
                    "rfid_status": movement.rfid_status,
                    "user_id": movement.user_id,
                    "mysim_user_id": movement.mysim_user_id,
                    "allowed": allowed,
                },
            )

            return {
                "status": "ok",
                "reason": (
                    "pending_gt_ready_for_location"
                    if allowed
                    else "pending_gt_wrong_aisle"
                ),
                "epc": epc,
                "antenna": event.antenna,
                "reader_id": reader_id,
                "logical_name": route.logical_name,
                "location_id": route.location_id,
                "zone": route.zone_id,
                "zone_role": route.zone_role,
                "route_mode": "door_engine",
                "door_id": route.door_id,
                "movement_id": movement.id,
                "movement_code": "GT",
                "review_status": movement.review_status,
                "rfid_status": movement.rfid_status,
                "detected_aisle_id": movement.detected_aisle_id,
                "detected_aisle_code": storage_aisle_code,
                "to_location_id": movement.to_location_id,
                "allowed": allowed,
                "ref_key": f"{route.door_id}:{epc}",
            }

        if _is_entrance(route):
            pending.last_route = route

            log_rfid_event(
                db,
                event_type="movement_updated",
                reason="pending_gt_seen_at_entrance",
                epc=epc,
                reader_id=reader_id,
                antenna=event.antenna,
                door_id=route.door_id,
                zone_id=route.zone_id,
                zone_role=route.zone_role,
                movement_code="GT",
                payload_json={
                    "movement_id": movement.id,
                    "last_seen_aisle": "ENTRANCE",
                    "expires_at": pending.expires_at,
                    "review_status": movement.review_status,
                    "rfid_status": movement.rfid_status,
                },
            )

            return {
                "status": "ok",
                "reason": "pending_gt_seen_at_entrance",
                "epc": epc,
                "antenna": event.antenna,
                "reader_id": reader_id,
                "door_id": route.door_id,
                "zone": route.zone_id,
                "zone_role": route.zone_role,
                "movement_id": movement.id,
                "movement_code": "GT",
                "review_status": movement.review_status,
                "rfid_status": movement.rfid_status,
                "last_seen_aisle": "ENTRANCE",
            }

    return {
        "status": "ok",
        "reason": "pending_movement_still_open",
        "epc": epc,
        "antenna": event.antenna,
        "reader_id": reader_id,
        "door_id": route.door_id,
        "zone": route.zone_id,
        "zone_role": route.zone_role,
        "movement_id": movement.id,
        "movement_code": pending.movement_code,
    }