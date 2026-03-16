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
from warehouse18.application.rfid.movement_service import finalize_movement_for_user
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
class DoorState:
    state: str
    ts: float
    route: RouteConfig
    cooldown_until: float = 0.0
    seen_count_same_side: int = 1


@dataclass
class PendingUserCross:
    created_at: float
    expires_at: float
    epc: str
    antenna: int
    reader_id: str
    rssi: float | None
    current_route: RouteConfig
    previous_route: RouteConfig
    movement_code: str
    route_label: str


_epc_schema: EPCSchema | None = None
_route_index: dict[tuple[str, int], RouteConfig] | None = None

_current_user_by_door: dict[str, dict[str, Any]] = {}
_last_seen_reader_event: dict[tuple[str, int, str], float] = {}
_epc_state_by_door: dict[tuple[str, str], DoorState] = {}
_pending_cross_by_door_epc: dict[tuple[str, str], PendingUserCross] = {}


def _reload_runtime_config() -> None:
    global USER_PRESENCE_TTL_S
    global USER_BIND_TTL_S
    global USER_COOLDOWN_S
    global READER_DEDUPE_S
    global CROSS_WINDOW_S
    global MOVE_COOLDOWN_S
    global STATE_TTL_S
    global MIN_SEEN_COUNT_TO_CONFIRM
    global PENDING_USER_WINDOW_S

    USER_PRESENCE_TTL_S = int(os.getenv("WAREHOUSE18_RFID_USER_PRESENCE_TTL_SECONDS", "600"))
    USER_BIND_TTL_S = int(os.getenv("WAREHOUSE18_RFID_USER_BIND_TTL_SECONDS", "20"))
    USER_COOLDOWN_S = float(os.getenv("WAREHOUSE18_RFID_USER_COOLDOWN_SECONDS", "2"))
    READER_DEDUPE_S = float(os.getenv("WAREHOUSE18_RFID_READER_DEDUPE_SECONDS", "0.6"))
    CROSS_WINDOW_S = float(os.getenv("WAREHOUSE18_RFID_CROSS_WINDOW_SECONDS", "6"))
    MOVE_COOLDOWN_S = float(os.getenv("WAREHOUSE18_RFID_MOVE_COOLDOWN_SECONDS", "5"))
    STATE_TTL_S = float(os.getenv("WAREHOUSE18_RFID_STATE_TTL_SECONDS", "20"))
    MIN_SEEN_COUNT_TO_CONFIRM = int(os.getenv("WAREHOUSE18_RFID_MIN_SEEN_COUNT_TO_CONFIRM", "1"))
    PENDING_USER_WINDOW_S = float(os.getenv("WAREHOUSE18_RFID_PENDING_USER_WINDOW_SECONDS", "3"))

    log.warning(
        "RFID CONFIG RELOADED | CROSS_WINDOW_S=%s PENDING_USER_WINDOW_S=%s MIN_SEEN_COUNT_TO_CONFIRM=%s",
        CROSS_WINDOW_S,
        PENDING_USER_WINDOW_S,
        MIN_SEEN_COUNT_TO_CONFIRM,
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


def _cleanup_epc_states(now_ts: float) -> None:
    expired = [
        key
        for key, state in _epc_state_by_door.items()
        if (now_ts - state.ts) > STATE_TTL_S and now_ts >= state.cooldown_until
    ]
    for key in expired:
        _epc_state_by_door.pop(key, None)


def _cleanup_pending_crosses(now_ts: float) -> None:
    expired = [
        key
        for key, pending in _pending_cross_by_door_epc.items()
        if now_ts > pending.expires_at
    ]
    for key in expired:
        pending = _pending_cross_by_door_epc.pop(key, None)
        if pending is not None:
            log.info(
                "RFID pending cross expired | door_id=%s epc=%s route=%s age=%.3f window=%.3f",
                pending.current_route.door_id,
                pending.epc,
                pending.route_label,
                now_ts - pending.created_at,
                PENDING_USER_WINDOW_S,
            )


def _find_recent_user_for_door(door_id: str, now_ts: float) -> int | None:
    data = _current_user_by_door.get(door_id)
    if not data:
        return None
    if (now_ts - float(data["ts"])) > USER_BIND_TTL_S:
        return None
    return int(data["user_id"])


def _start_or_refresh_state(door_id: str, epc: str, now_ts: float, route: RouteConfig) -> dict[str, Any]:
    state = DoorState(
        state=f"SEEN_{route.zone_role}",
        ts=now_ts,
        route=route,
        cooldown_until=0.0,
        seen_count_same_side=1,
    )
    _epc_state_by_door[(door_id, epc)] = state

    log.info(
        "RFID cross started | door_id=%s reader_id=%s epc=%s state=%s zone=%s antenna=%s",
        door_id,
        route.reader_id,
        epc,
        state.state,
        route.zone_id,
        route.antenna,
    )

    return {
        "status": "ok",
        "reason": "awaiting_cross",
        "epc": epc,
        "antenna": route.antenna,
        "reader_id": route.reader_id,
        "logical_name": route.logical_name,
        "location_id": route.location_id,
        "zone": route.zone_id,
        "route_mode": "door_engine",
        "door_id": route.door_id,
        "zone_role": route.zone_role,
        "ref_key": f"{door_id}:{epc}",
    }


def _try_resolve_pending_crosses_for_user(
    *,
    db: Session,
    door_id: str,
    mysim_user_id: int,
    now_ts: float,
) -> dict[str, Any] | None:
    candidates: list[tuple[tuple[str, str], PendingUserCross]] = [
        (key, pending)
        for key, pending in _pending_cross_by_door_epc.items()
        if key[0] == door_id and now_ts <= pending.expires_at
    ]

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[1].created_at, reverse=True)
    key, pending = candidates[0]

    log.info(
        "RFID pending cross resolved by late user | door_id=%s epc=%s route=%s user_id=%s lag=%.3f",
        door_id,
        pending.epc,
        pending.route_label,
        mysim_user_id,
        now_ts - pending.created_at,
    )

    _pending_cross_by_door_epc.pop(key, None)

    log_rfid_event(
        db,
        event_type="pending_resolved",
        reason="late_user_resolution",
        epc=pending.epc,
        reader_id=pending.reader_id,
        antenna=pending.antenna,
        door_id=door_id,
        zone_id=pending.current_route.zone_id,
        zone_role=pending.current_route.zone_role,
        movement_code=pending.movement_code,
        mysim_user_id=mysim_user_id,
        payload_json={
            "route": pending.route_label,
            "lag_seconds": round(now_ts - pending.created_at, 3),
        },
    )

    return finalize_movement_for_user(
        db=db,
        epc=pending.epc,
        epc_schema_path=str(EPC_SCHEMA_PATH),
        antenna=pending.antenna,
        reader_id=pending.reader_id,
        rssi=pending.rssi,
        current_route=pending.current_route,
        previous_route=pending.previous_route,
        movement_code=pending.movement_code,
        route_label=pending.route_label,
        mysim_user_id=mysim_user_id,
    )


def process_event(db: Session, event: RFIDEvent) -> dict[str, Any]:
    _reload_runtime_config()

    now_ts = time.time()
    epc = event.epc.strip().upper()
    reader_id = event.reader_id.strip() or "reader-1"

    _cleanup_user_bindings(now_ts)
    _cleanup_reader_dedupe(now_ts)
    _cleanup_epc_states(now_ts)
    _cleanup_pending_crosses(now_ts)

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
                mysim_user_id=serial_num,
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

        resolved = _try_resolve_pending_crosses_for_user(
            db=db,
            door_id=route.door_id,
            mysim_user_id=serial_num,
            now_ts=now_ts,
        )

        if resolved is not None:
            resolved["user_bind_reason"] = "late_user_resolution"
            return resolved

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
            mysim_user_id=serial_num,
            payload_json={
                "logical_name": route.logical_name,
                "location_id": route.location_id,
                "presence_ttl_seconds": USER_PRESENCE_TTL_S,
                "bind_ttl_seconds": USER_BIND_TTL_S,
            },
        )

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

    state_key = (route.door_id, epc)
    state = _epc_state_by_door.get(state_key)

    if state is None:
        result = _start_or_refresh_state(route.door_id, epc, now_ts, route)
        log_rfid_event(
            db,
            event_type="cross_started",
            reason="awaiting_cross",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            payload_json=result,
        )
        return result

    if now_ts < state.cooldown_until:
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
            payload_json={"cooldown_remaining": round(state.cooldown_until - now_ts, 3)},
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
            "cooldown_remaining": round(state.cooldown_until - now_ts, 3),
        }

    delta_s = now_ts - state.ts
    if delta_s > CROSS_WINDOW_S:
        log.info(
            "RFID cross expired | door_id=%s epc=%s prev_role=%s current_role=%s delta=%.3f window=%.3f",
            route.door_id,
            epc,
            state.route.zone_role,
            route.zone_role,
            delta_s,
            CROSS_WINDOW_S,
        )
        log_rfid_event(
            db,
            event_type="cross_expired",
            reason="cross_expired",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            payload_json={
                "prev_role": state.route.zone_role,
                "current_role": route.zone_role,
                "delta_seconds": round(delta_s, 3),
                "window_seconds": CROSS_WINDOW_S,
            },
        )
        result = _start_or_refresh_state(route.door_id, epc, now_ts, route)
        log_rfid_event(
            db,
            event_type="cross_started",
            reason="awaiting_cross",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            payload_json=result,
        )
        return result

    if state.route.zone_role == route.zone_role:
        state.ts = now_ts
        state.route = route
        state.seen_count_same_side += 1

        log.info(
            "RFID bounce same side | door_id=%s epc=%s role=%s count=%s",
            route.door_id,
            epc,
            route.zone_role,
            state.seen_count_same_side,
        )

        log_rfid_event(
            db,
            event_type="bounce_same_side",
            reason="bounce_same_side",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            payload_json={"seen_count_same_side": state.seen_count_same_side},
        )

        return {
            "status": "ok",
            "reason": "bounce_same_side",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "door_id": route.door_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
            "state": state.state,
            "seen_count_same_side": state.seen_count_same_side,
        }

    if state.route.zone_role == "A" and route.zone_role == "B":
        movement_code = os.getenv("WAREHOUSE18_RFID_MOVEMENT_A_TO_B", "GI").strip().upper()
        route_label = "A->B"
    elif state.route.zone_role == "B" and route.zone_role == "A":
        movement_code = os.getenv("WAREHOUSE18_RFID_MOVEMENT_B_TO_A", "GR").strip().upper()
        route_label = "B->A"
    else:
        result = _start_or_refresh_state(route.door_id, epc, now_ts, route)
        log_rfid_event(
            db,
            event_type="cross_started",
            reason="awaiting_cross",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            payload_json=result,
        )
        return result

    if state.seen_count_same_side < MIN_SEEN_COUNT_TO_CONFIRM:
        log.info(
            "RFID cross rejected weak evidence | door_id=%s epc=%s route=%s seen_count_same_side=%s min_required=%s",
            route.door_id,
            epc,
            route_label,
            state.seen_count_same_side,
            MIN_SEEN_COUNT_TO_CONFIRM,
        )
        log_rfid_event(
            db,
            event_type="cross_rejected_weak_evidence",
            reason="cross_rejected_weak_evidence",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            movement_code=movement_code,
            payload_json={
                "route": route_label,
                "seen_count_same_side": state.seen_count_same_side,
                "min_required": MIN_SEEN_COUNT_TO_CONFIRM,
            },
        )
        result = _start_or_refresh_state(route.door_id, epc, now_ts, route)
        log_rfid_event(
            db,
            event_type="cross_started",
            reason="awaiting_cross",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            payload_json=result,
        )
        return result

    prev_zone_id = state.route.zone_id

    log.info(
        "RFID cross accepted | door_id=%s epc=%s reader_id=%s route=%s movement_code=%s prev_zone=%s current_zone=%s",
        route.door_id,
        epc,
        reader_id,
        route_label,
        movement_code,
        prev_zone_id,
        route.zone_id,
    )

    log_rfid_event(
        db,
        event_type="cross_accepted",
        reason="cross_accepted",
        epc=epc,
        reader_id=reader_id,
        antenna=event.antenna,
        door_id=route.door_id,
        zone_id=route.zone_id,
        zone_role=route.zone_role,
        movement_code=movement_code,
        payload_json={
            "route": route_label,
            "prev_zone": prev_zone_id,
            "current_zone": route.zone_id,
        },
    )

    previous_route = state.route
    state.ts = now_ts
    state.route = route
    state.cooldown_until = now_ts + MOVE_COOLDOWN_S
    state.seen_count_same_side = 1

    mysim_user_id = _find_recent_user_for_door(route.door_id, now_ts)
    if mysim_user_id is None:
        pending = PendingUserCross(
            created_at=now_ts,
            expires_at=now_ts + PENDING_USER_WINDOW_S,
            epc=epc,
            antenna=event.antenna,
            reader_id=reader_id,
            rssi=event.rssi,
            current_route=route,
            previous_route=previous_route,
            movement_code=movement_code,
            route_label=route_label,
        )
        _pending_cross_by_door_epc[(route.door_id, epc)] = pending

        log.info(
            "RFID cross pending user resolution | door_id=%s epc=%s route=%s window=%.3f",
            route.door_id,
            epc,
            route_label,
            PENDING_USER_WINDOW_S,
        )

        log_rfid_event(
            db,
            event_type="pending_user_resolution",
            reason="pending_user_resolution",
            epc=epc,
            reader_id=reader_id,
            antenna=event.antenna,
            door_id=route.door_id,
            zone_id=route.zone_id,
            zone_role=route.zone_role,
            movement_code=movement_code,
            payload_json={
                "route": route_label,
                "pending_user_window_seconds": PENDING_USER_WINDOW_S,
            },
        )

        return {
            "status": "ok",
            "reason": "pending_user_resolution",
            "epc": epc,
            "antenna": event.antenna,
            "reader_id": reader_id,
            "logical_name": route.logical_name,
            "location_id": route.location_id,
            "zone": route.zone_id,
            "zone_role": route.zone_role,
            "route_mode": "door_engine",
            "door_id": route.door_id,
            "route": route_label,
            "movement_code": movement_code,
            "ref_key": f"{route.door_id}:{epc}",
            "pending_user_window_seconds": PENDING_USER_WINDOW_S,
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
            movement_code=movement_code,
            mysim_user_id=mysim_user_id,
            payload_json={"route": route_label},
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
            "route": route_label,
            "movement_code": movement_code,
            "user_id": mysim_user_id,
            "ref_key": f"{route.door_id}:{epc}",
        }

    return finalize_movement_for_user(
        db=db,
        epc=epc,
        epc_schema_path=str(EPC_SCHEMA_PATH),
        antenna=event.antenna,
        reader_id=reader_id,
        rssi=event.rssi,
        current_route=route,
        previous_route=previous_route,
        movement_code=movement_code,
        route_label=route_label,
        mysim_user_id=mysim_user_id,
    )