from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse18.domain.models.user import User
from warehouse18.infrastructure.db import get_db
from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter
from warehouse18.infrastructure.integrations.mySim.client import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.errors import MySimError
from warehouse18.presentation.api.schemas import ItemLocationOut

router = APIRouter(prefix="/mysim", tags=["mysim"])


MYSIM_MOVEMENT_TYPE_NAMES: dict[int, str] = {
    57: "Good Receipt",
    58: "Good Issue",
    59: "Good Transfer",
}


def _resolve_grouped_location_label(db: Session, external_location_id: object) -> str | None:
    if external_location_id in (None, ""):
        return None

    external_id = str(external_location_id).strip()

    row = db.execute(
        text(
            """
            SELECT
                g.display_name,
                g.code
            FROM public.mysim_location_group_ids i
            JOIN public.mysim_location_groups g
              ON g.id = i.mysim_location_group_id
            WHERE i.external_id = :external_id
            LIMIT 1
            """
        ),
        {"external_id": external_id},
    ).mappings().first()

    if row:
        return row["display_name"] or row["code"] or external_id

    return external_id


def _resolve_done_by_username(db: Session, done_by: object) -> str | None:
    if done_by in (None, ""):
        return None

    try:
        done_by_int = int(done_by)
    except (TypeError, ValueError):
        return str(done_by)

    user = (
        db.query(User)
        .filter(User.mysim_id == done_by_int)
        .first()
    )

    if not user:
        return str(done_by_int)

    return user.username or str(done_by_int)


def _resolve_movement_type_name(movement_type: object) -> str | None:
    if movement_type in (None, ""):
        return None

    try:
        movement_type_int = int(movement_type)
    except (TypeError, ValueError):
        return str(movement_type)

    return MYSIM_MOVEMENT_TYPE_NAMES.get(movement_type_int, str(movement_type_int))


@router.get("/item-location", response_model=ItemLocationOut)
def get_item_location(
    part_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    cfg = MySimConfig.from_env()
    client = MySimClient(cfg)
    adapter = MySimAdapter(client)

    try:
        last_mv = adapter.get_last_item_movement(item_id=part_id, item_entity="Parts")
    except MySimError as e:
        if getattr(e, "status_code", None) == 404:
            return ItemLocationOut(
                item_key=str(part_id),
                found=False,
            )
        raise

    if not last_mv:
        return ItemLocationOut(
            item_key=str(part_id),
            found=False,
        )

    destination_location = last_mv.get("destinationLocation")
    source_location = last_mv.get("sourceLocation")
    movement_id = last_mv.get("movementId") or last_mv.get("id")
    movement_type = last_mv.get("movementType")
    done_by = last_mv.get("doneBy")
    movement_date = (
        last_mv.get("date")
        or last_mv.get("created")
        or last_mv.get("lastUpdated")
    )

    source_location_label = _resolve_grouped_location_label(db, source_location)
    destination_location_label = _resolve_grouped_location_label(db, destination_location)
    done_by_name = _resolve_done_by_username(db, done_by)
    movement_type_name = _resolve_movement_type_name(movement_type)

    return ItemLocationOut(
        item_key=str(part_id),
        found=True,
        part_db_id=part_id,
        last_movement_id=str(movement_id) if movement_id is not None else None,
        movement_type=str(movement_type) if movement_type is not None else None,
        movement_type_name=movement_type_name,
        source_location=int(source_location) if source_location not in (None, "") else None,
        source_location_name=source_location_label,
        destination_location=int(destination_location) if destination_location not in (None, "") else None,
        destination_location_name=destination_location_label,
        destination_location_label=destination_location_label,
        done_by=int(done_by) if done_by not in (None, "") else None,
        done_by_name=done_by_name,
        movement_date=str(movement_date) if movement_date is not None else None,
        raw=last_mv,
    )