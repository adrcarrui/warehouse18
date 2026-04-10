from __future__ import annotations
import os
import os

os.environ["MYSIM_BASE_URL"] = "https://tests.simeng.es/api/v1/pub"
os.environ["MYSIM_TOKEN"] = "8b77da7fd1c738a3b4befb72dc28e43ac7f5db0e431831571fe9b53aa364fc5e"
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import requests
from sqlalchemy.orm import Session

from warehouse18.domain.models.location import Location
from warehouse18.domain.models.movement import Movement
from warehouse18.domain.models.movement_type import MovementType
from warehouse18.domain.models.user import User

def _log(msg: str) -> None:
    print(f"[mysim_sync] {msg}")


def _movement_debug_dict(movement: Movement) -> dict[str, Any]:
    return {
        "id": getattr(movement, "id", None),
        "movement_type_id": getattr(movement, "movement_type_id", None),
        "item_id": getattr(movement, "item_id", None),
        "mysim_item_id": getattr(movement, "mysim_item_id", None),
        "quantity": getattr(movement, "quantity", None),
        "from_location_id": getattr(movement, "from_location_id", None),
        "to_location_id": getattr(movement, "to_location_id", None),
        "user_id": getattr(movement, "user_id", None),
        "mysim_user_id": getattr(movement, "mysim_user_id", None),
        "review_status": getattr(movement, "review_status", None),
        "mysim_sync_status": getattr(movement, "mysim_sync_status", None),
        "mysim_movement_id": getattr(movement, "mysim_movement_id", None),
        "notes": getattr(movement, "notes", None),
        "reference_type": getattr(movement, "reference_type", None),
        "reference_id": getattr(movement, "reference_id", None),
    }

def _get_mysim_config() -> tuple[str, str, float]:
    base_url = os.getenv("MYSIM_BASE_URL", "").rstrip("/")
    token = os.getenv("MYSIM_TOKEN", "").strip()
    timeout = float(os.getenv("MYSIM_TIMEOUT_SECONDS", "30"))

    _log(
        f"_get_mysim_config | base_url={'set' if base_url else 'empty'} "
        f"token={'set' if token else 'empty'} timeout={timeout}"
    )

    if not base_url:
        raise RuntimeError("MYSIM_BASE_URL is empty")
    if not token:
        raise RuntimeError("MYSIM_TOKEN is empty")

    return base_url, token, timeout


def _get_movement_or_raise(db: Session, movement_id: int) -> Movement:
    _log(f"_get_movement_or_raise | movement_id={movement_id}")
    movement = db.query(Movement).filter(Movement.id == movement_id).first()
    if movement is None:
        raise RuntimeError(f"Movement not found: {movement_id}")

    _log(
        "_get_movement_or_raise | found movement="
        + json.dumps(_movement_debug_dict(movement), ensure_ascii=False, default=str)
    )
    return movement


def _get_movement_type_name(db: Session, movement_type_id: int | None) -> str:
    _log(f"_get_movement_type_name | movement_type_id={movement_type_id}")

    if movement_type_id is None:
        raise RuntimeError("movement_type_id is null")

    mt = db.query(MovementType).filter(MovementType.id == movement_type_id).first()
    if mt is None:
        raise RuntimeError(f"MovementType not found for id={movement_type_id}")

    name = getattr(mt, "name", None)
    if not name:
        raise RuntimeError(f"MovementType name missing for id={movement_type_id}")

    _log(f"_get_movement_type_name | resolved name={name}")
    return str(name)


def _map_movement_type_to_mysim(name: str) -> str:
    normalized = name.strip().lower()
    _log(f"_map_movement_type_to_mysim | input={name!r} normalized={normalized!r}")

    mapping = {
        "goods issue": "Good issue",
        "good issue": "Good issue",
        "goods receipt": "Good receipt",
        "good receipt": "Good receipt",
        "goods transfer": "Good transfer",
        "good transfer": "Good transfer",
        "goods tracking": "Good tracking",
        "good tracking": "Good tracking",
    }

    mysim_name = mapping.get(normalized)
    if not mysim_name:
        raise RuntimeError(f"Unsupported movement type for mySim: {name}")

    _log(f"_map_movement_type_to_mysim | resolved mysim_name={mysim_name}")
    return mysim_name


def _resolve_mysim_location_id(db: Session, local_location_id: int | None) -> int | None:
    _log(f"_resolve_mysim_location_id | local_location_id={local_location_id}")

    if local_location_id is None:
        _log("_resolve_mysim_location_id | local_location_id is None -> returning None")
        return None

    loc = db.query(Location).filter(Location.id == local_location_id).first()
    if loc is None:
        raise RuntimeError(f"Location not found for local id={local_location_id}")

    code = getattr(loc, "code", None)

    _log(
        f"_resolve_mysim_location_id | location_found id={getattr(loc, 'id', None)} "
        f"code={code} name={getattr(loc, 'name', None)}"
    )

    if code is None:
        raise RuntimeError(f"Location local id={local_location_id} has no code")

    code_str = str(code).strip()
    if not code_str:
        raise RuntimeError(f"Location local id={local_location_id} has empty code")

    try:
        resolved = int(code_str)
    except ValueError:
        raise RuntimeError(
            f"Location local id={local_location_id} has non-numeric code={code_str!r}"
        )

    _log(
        f"_resolve_mysim_location_id | resolved from code raw={code_str!r} resolved={resolved}"
    )
    return resolved


def _resolve_mysim_user_id(
    db: Session,
    *,
    local_user_id: int | None,
    explicit_mysim_user_id: int | None,
) -> int | None:
    _log(
        f"_resolve_mysim_user_id | local_user_id={local_user_id} "
        f"explicit_mysim_user_id={explicit_mysim_user_id}"
    )

    if explicit_mysim_user_id is not None:
        _log(f"_resolve_mysim_user_id | using explicit mysim_user_id={explicit_mysim_user_id}")
        return int(explicit_mysim_user_id)

    if local_user_id is None:
        _log("_resolve_mysim_user_id | local_user_id is None -> returning None")
        return None

    user = db.query(User).filter(User.id == local_user_id).first()
    if user is None:
        raise RuntimeError(f"User not found for local id={local_user_id}")

    mysim_id = getattr(user, "mysim_id", None)
    _log(
        f"_resolve_mysim_user_id | user_found id={getattr(user, 'id', None)} "
        f"name={getattr(user, 'name', None)} mysim_id={mysim_id}"
    )

    if mysim_id is None:
        raise RuntimeError(f"User local id={local_user_id} has no mysim_id")

    return int(mysim_id)


def _resolve_item_identifier(movement: Movement) -> int | str:
    """
    Orden de resolución:
    1) movement.mysim_item_id si existiera en el modelo
    2) movement.item_id
    3) movement.item_key, extrayendo lo que va después del guion
       Ej: CN235-015992 -> 15992
    """
    mysim_item_id = getattr(movement, "mysim_item_id", None)
    item_id = getattr(movement, "item_id", None)
    item_key = getattr(movement, "item_key", None)

    _log(
        f"_resolve_item_identifier | movement_id={movement.id} "
        f"mysim_item_id={mysim_item_id} item_id={item_id} item_key={item_key!r} "
        f"reference_type={getattr(movement, 'reference_type', None)} "
        f"reference_id={getattr(movement, 'reference_id', None)}"
    )

    if mysim_item_id is not None:
        _log(f"_resolve_item_identifier | using mysim_item_id={mysim_item_id}")
        return int(mysim_item_id)

    if item_id is not None:
        _log(f"_resolve_item_identifier | using item_id={item_id}")
        return int(item_id)

    if item_key:
        raw = str(item_key).strip()

        if "-" not in raw:
            raise RuntimeError(
                f"item_key has no '-' separator for movement_id={movement.id}: {raw}"
            )

        suffix = raw.split("-", 1)[1].strip()

        if not suffix:
            raise RuntimeError(
                f"item_key suffix is empty for movement_id={movement.id}: {raw}"
            )

        if not suffix.isdigit():
            raise RuntimeError(
                f"item_key suffix is not numeric for movement_id={movement.id}: {raw}"
            )

        resolved = int(suffix)
        _log(
            f"_resolve_item_identifier | parsed from item_key raw={raw} "
            f"suffix={suffix} resolved={resolved}"
        )
        return resolved

    raise RuntimeError(f"Unable to resolve item identifier for movement_id={movement.id}")


def _normalize_quantity(raw: Any) -> int | float:
    _log(f"_normalize_quantity | raw={raw!r} type={type(raw).__name__}")

    if raw is None:
        _log("_normalize_quantity | raw is None -> 1")
        return 1
    if isinstance(raw, Decimal):
        raw = float(raw)
    if raw == "" or raw == 0 or raw == "0":
        _log("_normalize_quantity | raw empty/zero -> 1")
        return 1

    try:
        value = float(raw)
    except Exception:
        _log("_normalize_quantity | could not cast to float -> 1")
        return 1

    if value.is_integer():
        normalized = int(value)
        _log(f"_normalize_quantity | normalized int={normalized}")
        return normalized

    _log(f"_normalize_quantity | normalized float={value}")
    return value


def _build_description(movement: Movement) -> str:
    base = f"W18:{movement.id}"
    note = getattr(movement, "notes", None)
    description = f"{base} - {note}" if note else base
    _log(f"_build_description | movement_id={movement.id} description={description!r}")
    return description


def _build_mysim_payload(db: Session, movement: Movement) -> list[dict[str, Any]]:
    _log(
        "_build_mysim_payload | start movement="
        + json.dumps(_movement_debug_dict(movement), ensure_ascii=False, default=str)
    )

    movement_type_name = _get_movement_type_name(db, movement.movement_type_id)
    mysim_movement_type = _map_movement_type_to_mysim(movement_type_name)

    item_identifier = _resolve_item_identifier(movement)
    source_location = _resolve_mysim_location_id(db, getattr(movement, "from_location_id", None))
    destination_location = _resolve_mysim_location_id(db, getattr(movement, "to_location_id", None))
    done_by = _resolve_mysim_user_id(
        db,
        local_user_id=getattr(movement, "user_id", None),
        explicit_mysim_user_id=getattr(movement, "mysim_user_id", None),
    )
    created_at = getattr(movement, "created_at", None)
    quantity = _normalize_quantity(getattr(movement, "quantity", None))
    description = _build_description(movement)

    row: dict[str, Any] = {
        "entity": "Parts",
        "idCol": item_identifier,
        "movementType": mysim_movement_type,
        "quantity": quantity,
        "movementDescription": description,
        "date": created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else None,
    }

    if source_location is not None:
        row["sourceLocation"] = source_location

    if destination_location is not None:
        row["destinationLocation"] = destination_location

    if done_by is not None:
        row["doneBy"] = done_by

    payload = [row]

    _log(
        "_build_mysim_payload | payload="
        + json.dumps(payload, ensure_ascii=False, default=str)
    )

    return payload


def _post_to_mysim(entity: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
    _log(f"_post_to_mysim | env_now base_url={os.getenv('MYSIM_BASE_URL')!r} token_present={bool(os.getenv('MYSIM_TOKEN'))}")
    base_url, token, timeout = _get_mysim_config()  

    url = f"{base_url}/set?entity={entity}"
    headers = {
        "X-AUTH-TOKEN": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    _log(f"_post_to_mysim | POST {url}")
    _log(
        "_post_to_mysim | payload="
        + json.dumps(payload, ensure_ascii=False, default=str)
    )

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=timeout,
        allow_redirects=True,
    )

    content_type = response.headers.get("content-type", "").lower()
    text_body = response.text[:2000]

    _log(
        f"_post_to_mysim | response status_code={response.status_code} "
        f"content_type={content_type!r} history_len={len(response.history)}"
    )

    if response.history:
        history_summary = [
            {
                "status_code": h.status_code,
                "location": h.headers.get("location"),
                "url": getattr(h.request, "url", None),
            }
            for h in response.history
        ]
        _log(
            "_post_to_mysim | redirect_history="
            + json.dumps(history_summary, ensure_ascii=False, default=str)
        )
        raise RuntimeError(
            f"mySim returned redirect chain while calling {url}. "
            f"final_status={response.status_code} body={text_body}"
        )

    if "application/json" not in content_type:
        _log(f"_post_to_mysim | non_json_body={text_body}")
        raise RuntimeError(
            f"mySim did not return JSON. status={response.status_code} "
            f"content_type={content_type} body={text_body}"
        )

    data = response.json()
    _log(
        "_post_to_mysim | response_json="
        + json.dumps(data, ensure_ascii=False, default=str)[:4000]
    )

    inner_status = data.get("status")
    if response.status_code != 200 or inner_status not in (200, "200", None):
        raise RuntimeError(
            f"mySim set failed. http_status={response.status_code} "
            f"json_status={inner_status} body={text_body}"
        )

    return data


def _extract_mysim_movement_id(response_json: dict[str, Any]) -> str:
    _log(
        "_extract_mysim_movement_id | response_json="
        + json.dumps(response_json, ensure_ascii=False, default=str)[:4000]
    )

    last_object = (
        response_json.get("data", {})
        .get("data", {})
        .get("lastObject", {})
    )

    mysim_id = last_object.get("id")
    if mysim_id is None:
        raise RuntimeError("mySim response missing data.data.lastObject.id")

    _log(f"_extract_mysim_movement_id | resolved mysim_id={mysim_id}")
    return str(mysim_id)


def _upload_movement_to_mysim(db: Session, movement: Movement) -> str:
    _log(f"_upload_movement_to_mysim | movement_id={movement.id}")
    payload = _build_mysim_payload(db, movement)
    response_json = _post_to_mysim("movement", payload)
    mysim_movement_id = _extract_mysim_movement_id(response_json)
    _log(
        f"_upload_movement_to_mysim | success movement_id={movement.id} "
        f"mysim_movement_id={mysim_movement_id}"
    )
    return mysim_movement_id


def sync_movement_to_mysim(db: Session, movement_id: int) -> Movement:
    _log(f"sync_movement_to_mysim | start movement_id={movement_id}")
    movement = _get_movement_or_raise(db, movement_id)

    _log(
        f"sync_movement_to_mysim | review_status={movement.review_status} "
        f"mysim_sync_status={getattr(movement, 'mysim_sync_status', None)}"
    )

    if str(movement.review_status).lower() != "confirmed":
        raise RuntimeError(
            f"Movement {movement_id} is not confirmed. review_status={movement.review_status}"
        )

    try:
        mysim_movement_id = _upload_movement_to_mysim(db, movement)

        movement.mysim_movement_id = mysim_movement_id
        movement.mysim_sync_status = "ok"
        movement.mysim_synced_at = datetime.now(timezone.utc)
        movement.mysim_sync_error = None

        db.add(movement)
        db.commit()
        db.refresh(movement)

        _log(
            f"sync_movement_to_mysim | success movement_id={movement_id} "
            f"mysim_movement_id={movement.mysim_movement_id}"
        )
        return movement

    except Exception as e:
        db.rollback()
        _log(
            f"sync_movement_to_mysim | exception movement_id={movement_id} "
            f"error={str(e)}"
        )

        movement = _get_movement_or_raise(db, movement_id)
        movement.mysim_sync_status = "error"
        movement.mysim_sync_error = str(e)[:2000]

        db.add(movement)
        db.commit()
        db.refresh(movement)

        _log(
            f"sync_movement_to_mysim | marked error movement_id={movement_id} "
            f"mysim_sync_error={movement.mysim_sync_error}"
        )
        raise