from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import requests
from sqlalchemy.orm import Session

from warehouse18.domain.models.location import Location
from warehouse18.domain.models.movement import Movement
from warehouse18.domain.models.movement_type import MovementType
from warehouse18.domain.models.user import User


MYSIM_BASE_URL = os.getenv("MYSIM_BASE_URL", "").rstrip("/")
MYSIM_TOKEN = os.getenv("MYSIM_TOKEN", "").strip()
MYSIM_TIMEOUT = float(os.getenv("MYSIM_TIMEOUT_SECONDS", "30"))


def _require_mysim_config() -> None:
    if not MYSIM_BASE_URL:
        raise RuntimeError("MYSIM_BASE_URL is empty")
    if not MYSIM_TOKEN:
        raise RuntimeError("MYSIM_TOKEN is empty")


def _get_movement_or_raise(db: Session, movement_id: int) -> Movement:
    movement = db.query(Movement).filter(Movement.id == movement_id).first()
    if movement is None:
        raise RuntimeError(f"Movement not found: {movement_id}")
    return movement


def _get_movement_type_name(db: Session, movement_type_id: int | None) -> str:
    if movement_type_id is None:
        raise RuntimeError("movement_type_id is null")

    mt = db.query(MovementType).filter(MovementType.id == movement_type_id).first()
    if mt is None:
        raise RuntimeError(f"MovementType not found for id={movement_type_id}")

    name = getattr(mt, "name", None)
    if not name:
        raise RuntimeError(f"MovementType name missing for id={movement_type_id}")

    return str(name)


def _map_movement_type_to_mysim(name: str) -> str:
    normalized = name.strip().lower()

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

    return mysim_name


def _resolve_mysim_location_id(db: Session, local_location_id: int | None) -> int | None:
    if local_location_id is None:
        return None

    loc = db.query(Location).filter(Location.id == local_location_id).first()
    if loc is None:
        raise RuntimeError(f"Location not found for local id={local_location_id}")

    mysim_id = getattr(loc, "mysim_id", None)
    if mysim_id is None:
        raise RuntimeError(f"Location local id={local_location_id} has no mysim_id")

    return int(mysim_id)


def _resolve_mysim_user_id(
    db: Session,
    *,
    local_user_id: int | None,
    explicit_mysim_user_id: int | None,
) -> int | None:
    if explicit_mysim_user_id is not None:
        return int(explicit_mysim_user_id)

    if local_user_id is None:
        return None

    user = db.query(User).filter(User.id == local_user_id).first()
    if user is None:
        raise RuntimeError(f"User not found for local id={local_user_id}")

    mysim_id = getattr(user, "mysim_id", None)
    if mysim_id is None:
        raise RuntimeError(f"User local id={local_user_id} has no mysim_id")

    return int(mysim_id)


def _resolve_item_identifier(movement: Movement) -> int | str:
    """
    Ajusta esta función si tu item_id local NO coincide con el id esperado por mySim.
    Si en tu integración ya usabas item_id como idCol válido para mySim, esto te sirve.
    """
    mysim_item_id = getattr(movement, "mysim_item_id", None)
    if mysim_item_id is not None:
        return mysim_item_id

    item_id = getattr(movement, "item_id", None)
    if item_id is not None:
        return item_id

    raise RuntimeError(f"Unable to resolve item identifier for movement_id={movement.id}")


def _normalize_quantity(raw: Any) -> int | float:
    if raw is None:
        return 1
    if isinstance(raw, Decimal):
        raw = float(raw)
    if raw == "" or raw == 0 or raw == "0":
        return 1

    try:
        value = float(raw)
    except Exception:
        return 1

    if value.is_integer():
        return int(value)
    return value


def _build_description(movement: Movement) -> str:
    base = f"W18:{movement.id}"
    note = getattr(movement, "notes", None)
    if note:
        return f"{base} - {note}"
    return base


def _build_mysim_payload(db: Session, movement: Movement) -> list[dict[str, Any]]:
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
    quantity = _normalize_quantity(getattr(movement, "quantity", None))
    description = _build_description(movement)

    row: dict[str, Any] = {
        "entity": "Parts",
        "idCol": item_identifier,
        "movementType": mysim_movement_type,
        "quantity": quantity,
        "movementDescription": description,
    }

    if source_location is not None:
        row["sourceLocation"] = source_location

    if destination_location is not None:
        row["destinationLocation"] = destination_location

    if done_by is not None:
        row["doneBy"] = done_by

    return [row]


def _post_to_mysim(entity: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
    _require_mysim_config()

    url = f"{MYSIM_BASE_URL}/set?entity={entity}"
    headers = {
        "X-AUTH-TOKEN": MYSIM_TOKEN,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=MYSIM_TIMEOUT,
        allow_redirects=True,
    )

    content_type = response.headers.get("content-type", "").lower()
    text_body = response.text[:2000]

    if response.history:
        raise RuntimeError(
            f"mySim returned redirect chain while calling {url}. "
            f"final_status={response.status_code} body={text_body}"
        )

    if "application/json" not in content_type:
        raise RuntimeError(
            f"mySim did not return JSON. status={response.status_code} "
            f"content_type={content_type} body={text_body}"
        )

    data = response.json()

    # La especificación devuelve status dentro del JSON también :contentReference[oaicite:1]{index=1}
    inner_status = data.get("status")
    if response.status_code != 200 or inner_status not in (200, "200", None):
        raise RuntimeError(
            f"mySim set failed. http_status={response.status_code} "
            f"json_status={inner_status} body={text_body}"
        )

    return data


def _extract_mysim_movement_id(response_json: dict[str, Any]) -> str:
    last_object = (
        response_json.get("data", {})
        .get("data", {})
        .get("lastObject", {})
    )

    mysim_id = last_object.get("id")
    if mysim_id is None:
        raise RuntimeError("mySim response missing data.data.lastObject.id")

    return str(mysim_id)


def _upload_movement_to_mysim(db: Session, movement: Movement) -> str:
    payload = _build_mysim_payload(db, movement)
    response_json = _post_to_mysim("movement", payload)
    return _extract_mysim_movement_id(response_json)


def sync_movement_to_mysim(db: Session, movement_id: int) -> Movement:
    movement = _get_movement_or_raise(db, movement_id)

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
        return movement

    except Exception as e:
        db.rollback()

        movement = _get_movement_or_raise(db, movement_id)
        movement.mysim_sync_status = "error"
        movement.mysim_sync_error = str(e)[:2000]

        db.add(movement)
        db.commit()
        db.refresh(movement)
        raise