from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.orm import Session

from warehouse18.application.rfid.epc96 import EPCSchema, load_epc_schema, parse_epc96
from warehouse18.application.rfid.event_log_service import log_rfid_event
from warehouse18.application.rfid.movement_service import (
    attach_user_to_movement_if_missing,
    complete_receipt_destination,
    create_preventive_movement,
    finalize_preventive_movement,
    get_movement_by_id,
    mutate_issue_to_transfer,
    resolve_local_location_id_by_mysim_code,
    resolve_local_user_by_mysim_id,
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


_epc_schema: EPCSchema | None = None
_route_index: dict[tuple[str, int], RouteConfig] | None = None

_current_user_by_door: dict[str, dict[str, Any]] = {}
_last_seen_reader_event: dict[tuple[str, int, str], float] = {}
_pending_movement_by_epc: dict[str, PendingMovement] = {}
_movement_cooldown_by_epc: dict[str, float] = {}


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
    MOVE_COOLDOWN_S = float(os.getenv("WAREHOUSE18_RFID_MOVE_COOLDOWN_SECONDS", "5"))
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


def _is_entrance(route: RouteConfig) -> bool:
    return route.aisle_id == "ENTRANCE"


def _is_aisle(route: RouteConfig) -> bool:
    return route.aisle_id.startswith("AISLE_")


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
        from_location_id_local = resolve_local_location_id_by_mysim_code(db, route.location_id)

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
            from_location_id_local=from_location_id_local,
            to_location_id_local=None,
        )

        pending = PendingMovement(
            movement_id=int(movement.id),
            movement_code="GI",
            created_at=now_ts,
            expires_at=now_ts + PREVENTIVE_ENRICH_WINDOW_S,
            door_id=route.door_id,
            first_route=route,
            from_location_id_local=from_location_id_local,
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
                "from_location_id_local": from_location_id_local,
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

    # GR preventivo + lectura posterior en pasillo -> completar destino
    if pending.movement_code == "GR":
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
            }

        if _is_aisle(route):
            to_location_id_local = resolve_local_location_id_by_mysim_code(db, route.location_id)
            movement = complete_receipt_destination(
                db,
                movement=movement,
                to_location_id_local=to_location_id_local,
                mysim_user_id=recent_mysim_user_id,
            )

            _pending_movement_by_epc.pop(epc, None)
            _movement_cooldown_by_epc[epc] = now_ts + MOVE_COOLDOWN_S

            log_rfid_event(
                db,
                event_type="movement_updated",
                reason="preventive_gr_completed_with_destination",
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
                    "route": f"{pending.first_route.aisle_id}->{route.aisle_id}",
                    "to_location_id_local": to_location_id_local,
                    "rfid_status": movement.rfid_status,
                    "review_status": movement.review_status,
                    "user_id": movement.user_id,
                    "mysim_user_id": movement.mysim_user_id,
                },
            )

            return {
                "status": "ok",
                "reason": "preventive_gr_completed",
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

    # GI preventivo + lectura en otro pasillo -> mutar a GT
    if pending.movement_code == "GI":
        if _is_aisle(route):
            to_location_id_local = resolve_local_location_id_by_mysim_code(db, route.location_id)

            if pending.from_location_id_local == to_location_id_local:
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
                }

            movement = mutate_issue_to_transfer(
                db,
                movement=movement,
                to_location_id_local=to_location_id_local,
                mysim_user_id=recent_mysim_user_id,
            )

            _pending_movement_by_epc.pop(epc, None)
            _movement_cooldown_by_epc[epc] = now_ts + MOVE_COOLDOWN_S

            log_rfid_event(
                db,
                event_type="movement_updated",
                reason="preventive_gi_mutated_to_gt",
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
                    "to_location_id_local": to_location_id_local,
                    "rfid_status": movement.rfid_status,
                    "review_status": movement.review_status,
                    "user_id": movement.user_id,
                    "mysim_user_id": movement.mysim_user_id,
                },
            )

            return {
                "status": "ok",
                "reason": "preventive_gi_mutated_to_gt",
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
                "ref_key": f"{route.door_id}:{epc}",
            }

        if _is_entrance(route):
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