from __future__ import annotations

import base64
import logging
import os
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import requests
from sqlalchemy.orm import Session

from warehouse18.application.rfid.epc96 import EPCSchema, load_epc_schema, parse_epc96
from warehouse18.application.rfid.event_log_service import log_rfid_event
from warehouse18.domain.models.movement import Movement
from warehouse18.domain.models.movement_type import MovementType as LocalMovementType
from warehouse18.domain.models.rfid_event_log import RfidEventLog
from warehouse18.domain.models.user import User
from warehouse18.infrastructure.integrations.mySim import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter
from warehouse18.infrastructure.integrations.mySim.errors import MySimError

log = logging.getLogger("warehouse18.rfid")


def mysim_client_and_adapter() -> tuple[MySimClient, MySimAdapter]:
    cfg = MySimConfig.from_env()
    log.info(
        "RFID mySim config | base_url=%s token_present=%s token_len=%s",
        cfg.base_url,
        bool(cfg.token),
        len(cfg.token or ""),
    )
    client = MySimClient(cfg)
    api = MySimAdapter(client)
    return client, api


def movement_type_by_code(db: Session, code: str) -> LocalMovementType | None:
    return db.query(LocalMovementType).filter(LocalMovementType.code == code).first()


def resolve_local_user_by_mysim_id(db: Session, mysim_user_id: int) -> User | None:
    return db.query(User).filter(User.mysim_id == mysim_user_id).first()


def build_item_key_from_epc(epc: str, epc_schema_path: str) -> str:
    schema: EPCSchema = load_epc_schema(epc_schema_path)
    parsed = parse_epc96(epc, schema)
    family = str(parsed.family_name or "UNKNOWN").strip().upper()
    serial_num = int(parsed.serial)
    return f"{family}-{serial_num:06d}"


def mysim_b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def mysim_movement_type_id(code: str) -> int:
    mapping = {"GR": 57, "GI": 58, "GT": 59}
    if code not in mapping:
        raise ValueError(f"movement_code no soportado para mySim: {code}")
    return mapping[code]


def mysim_movement_type_name(code: str) -> str:
    mapping = {"GR": "Good Receipt", "GI": "Good Issue", "GT": "Good Transfer"}
    if code not in mapping:
        raise ValueError(f"movement_code no soportado para mySim: {code}")
    return mapping[code]


def mysim_now_str() -> str:
    return datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S")


def mysim_location_for_route(route: Any) -> int:
    if not route.mysim_location_env:
        raise ValueError(
            f"La ruta {route.zone_id} no tiene mysim_location_env configurado en antenna_map.json"
        )

    raw = os.getenv(route.mysim_location_env)
    if not raw:
        raise ValueError(
            f"No existe la variable de entorno {route.mysim_location_env} para zone={route.zone_id}"
        )
    return int(raw)


def post_movement_direct(
    cfg: MySimConfig,
    row: dict[str, Any],
    *,
    allow_redirects: bool = False,
) -> dict[str, Any]:
    extra_query_expr = f"t.idCol='{row['idCol']}' AND t.entity='Parts'"
    extra_query = mysim_b64(extra_query_expr)

    url = f"{cfg.base_url.rstrip('/')}/set"
    params = {"entity": "movement", "extraQuery": extra_query}
    headers = {"Accept": "application/json", "X-AUTH-TOKEN": cfg.token}

    log.info("RFID -> mySim movement row | row=%s", row)

    resp = requests.post(
        url,
        headers=headers,
        params=params,
        json=[row],
        timeout=60,
        allow_redirects=allow_redirects,
    )

    if not resp.ok:
        payload: dict[str, Any] = {
            "status_code": resp.status_code,
            "location": resp.headers.get("Location"),
            "body_head": resp.text[:500],
        }
        raise MySimError(status_code=resp.status_code, payload=payload)

    try:
        return resp.json()
    except ValueError:
        return {"status_code": resp.status_code, "text": resp.text[:2000]}


def create_local_movement(
    db: Session,
    *,
    movement_code: str,
    epc: str,
    epc_schema_path: str,
    rssi: float | None,
    antenna: int,
    current_route: Any,
    previous_route: Any,
    local_user_id: int,
    mysim_user_id: int,
) -> tuple[bool, dict[str, Any] | str]:
    mt = movement_type_by_code(db, movement_code)
    if mt is None:
        return False, f"movement_type_not_found:{movement_code}"

    item_key = build_item_key_from_epc(epc, epc_schema_path)

    notes = (
        f"RFID app history | epc={epc} | door_id={current_route.door_id} | "
        f"reader_id={current_route.reader_id} | "
        f"route={previous_route.zone_role}->{current_route.zone_role} | "
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
        review_status="pending",
        mysim_sync_status="pending_review",
        reviewed_at=None,
        reviewed_by_user_id=None,
        review_note=None,
        mysim_synced_at=None,
        mysim_sync_error=None,
    )

    db.add(mv)
    db.commit()
    db.refresh(mv)

    payload = {
        "movement_id": int(mv.id),
        "item_key": item_key,
        "movement_code": movement_code,
    }

    log.info(
        "RFID local movement created (pending review) | movement_id=%s code=%s epc=%s item_key=%s local_user_id=%s mysim_user_id=%s",
        mv.id,
        movement_code,
        epc,
        item_key,
        local_user_id,
        mysim_user_id,
    )
    return True, payload


def build_mysim_sync_payload(
    *,
    movement_code: str,
    item_key: str,
    mysim_user_id: int,
    current_route: Any,
    previous_route: Any,
    description: str,
) -> dict[str, Any]:
    client, api = mysim_client_and_adapter()

    part_db_id = api.get_part_id_by_part_code(item_key)
    if part_db_id is None:
        raise ValueError(f"No se encontró partId={item_key} en mySim")

    movement_type_id = mysim_movement_type_id(movement_code)
    movement_type_name = mysim_movement_type_name(movement_code)

    source_location = mysim_location_for_route(previous_route)
    destination_location = mysim_location_for_route(current_route)

    row: dict[str, Any] = {
        "id": 0,
        "entity": "Parts",
        "idCol": int(part_db_id),
        "movementType": movement_type_id,
        "movementType.name": movement_type_name,
        "quantity": 1,
        "movementDescription": description,
        "date": mysim_now_str(),
        "doneBy": int(mysim_user_id),
        "sourceLocation": int(source_location),
        "destinationLocation": int(destination_location),
        "parentRecord": item_key,
    }

    return {
        "part_db_id": int(part_db_id),
        "item_key": item_key,
        "movement_type_id": movement_type_id,
        "movement_type_name": movement_type_name,
        "source_location": int(source_location),
        "destination_location": int(destination_location),
        "row": row,
    }


def sync_pending_reviewed_movement(
    db: Session,
    *,
    movement: Movement,
    movement_event: RfidEventLog,
) -> dict[str, Any]:
    payload = movement_event.payload_json or {}
    sync_payload = payload.get("mysim_sync_payload") or {}
    row = sync_payload.get("row")
    if not row:
        raise ValueError("movement_created event does not contain mysim_sync_payload.row")

    client, _api = mysim_client_and_adapter()
    resp = post_movement_direct(client.cfg, row)

    movement.mysim_sync_status = "ok"
    movement.mysim_synced_at = datetime.now(timezone.utc)
    movement.mysim_sync_error = None
    db.add(movement)
    db.commit()

    log_rfid_event(
        db,
        event_type="movement_sync_ok",
        reason="movement_sent",
        epc=movement_event.epc,
        reader_id=movement_event.reader_id,
        antenna=movement_event.antenna,
        door_id=movement_event.door_id,
        zone_id=movement_event.zone_id,
        zone_role=movement_event.zone_role,
        movement_code=movement_event.movement_code,
        movement_id=movement.id,
        user_id=movement.user_id,
        mysim_user_id=movement.mysim_user_id,
        payload_json={
            "mysim_row": row,
            "mysim_response": resp,
        },
        review_status="confirmed",
    )

    return {
        "status": "ok",
        "response": resp,
    }


def finalize_movement_for_user(
    *,
    db: Session,
    epc: str,
    epc_schema_path: str,
    antenna: int,
    reader_id: str,
    rssi: float | None,
    current_route: Any,
    previous_route: Any,
    movement_code: str,
    route_label: str,
    mysim_user_id: int,
) -> dict[str, Any]:
    local_user = resolve_local_user_by_mysim_id(db, mysim_user_id)
    if local_user is None:
        return {
            "status": "ignored",
            "reason": "local_user_not_found_for_mysim_id",
            "epc": epc,
            "antenna": antenna,
            "reader_id": reader_id,
            "logical_name": current_route.logical_name,
            "location_id": current_route.location_id,
            "zone": current_route.zone_id,
            "zone_role": current_route.zone_role,
            "route_mode": "door_engine",
            "door_id": current_route.door_id,
            "route": route_label,
            "movement_code": movement_code,
            "user_id": mysim_user_id,
            "ref_key": f"{current_route.door_id}:{epc}",
        }

    try:
        ok, local_result = create_local_movement(
            db,
            movement_code=movement_code,
            epc=epc,
            epc_schema_path=epc_schema_path,
            rssi=rssi,
            antenna=antenna,
            current_route=current_route,
            previous_route=previous_route,
            local_user_id=local_user.id,
            mysim_user_id=mysim_user_id,
        )
    except Exception as e:
        db.rollback()
        return {
            "status": "ignored",
            "reason": "db_integrity_error",
            "epc": epc,
            "antenna": antenna,
            "reader_id": reader_id,
            "logical_name": current_route.logical_name,
            "location_id": current_route.location_id,
            "zone": current_route.zone_id,
            "zone_role": current_route.zone_role,
            "detail": str(e),
            "movement_code": movement_code,
            "user_id": local_user.id,
            "mysim_user_id": mysim_user_id,
        }

    if not ok:
        return {
            "status": "ignored",
            "reason": str(local_result),
            "epc": epc,
            "antenna": antenna,
            "reader_id": reader_id,
            "logical_name": current_route.logical_name,
            "location_id": current_route.location_id,
            "zone": current_route.zone_id,
            "zone_role": current_route.zone_role,
            "movement_code": movement_code,
            "user_id": local_user.id,
            "mysim_user_id": mysim_user_id,
        }

    movement_id = int(local_result["movement_id"])
    item_key = str(local_result["item_key"])

    mysim_description = (
        f"RFID {route_label} | epc={epc} | item_key={item_key} | "
        f"door_id={current_route.door_id} | reader_id={reader_id} | antenna={antenna} | rssi={rssi}"
    )

    mysim_sync_payload = build_mysim_sync_payload(
        movement_code=movement_code,
        item_key=item_key,
        mysim_user_id=mysim_user_id,
        current_route=current_route,
        previous_route=previous_route,
        description=mysim_description,
    )

    log_rfid_event(
        db,
        event_type="movement_created",
        reason="movement_created_pending_review",
        epc=epc,
        reader_id=reader_id,
        antenna=antenna,
        door_id=current_route.door_id,
        zone_id=current_route.zone_id,
        zone_role=current_route.zone_role,
        movement_code=movement_code,
        movement_id=movement_id,
        user_id=local_user.id,
        mysim_user_id=mysim_user_id,
        review_status="pending",
        payload_json={
            "route": route_label,
            "item_key": item_key,
            "from_location_id": previous_route.location_id,
            "to_location_id": current_route.location_id,
            "mysim_sync_payload": mysim_sync_payload,
        },
    )

    return {
        "status": "ok",
        "reason": "movement_created_pending_review",
        "epc": epc,
        "antenna": antenna,
        "reader_id": reader_id,
        "logical_name": current_route.logical_name,
        "location_id": current_route.location_id,
        "zone": current_route.zone_id,
        "zone_role": current_route.zone_role,
        "route_mode": "door_engine",
        "door_id": current_route.door_id,
        "route": route_label,
        "movement_code": movement_code,
        "movement_id": movement_id,
        "item_key": item_key,
        "user_id": local_user.id,
        "mysim_user_id": mysim_user_id,
        "review_status": "pending",
        "mysim_sync": {
            "status": "pending_review",
            "reason": "manual_confirmation_required",
        },
    }