from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models.location import Location
from warehouse18.infrastructure.integrations.mySim.client import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter
from warehouse18.infrastructure.integrations.mySim.errors import MySimError
from warehouse18.presentation.api.schemas import ItemLocationOut

router = APIRouter(prefix="/mysim", tags=["mysim"])


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

    destination_location_label = None
    if destination_location is not None:
        loc = (
            db.query(Location)
            .filter(Location.code == str(destination_location))
            .first()
        )
        if loc:
            destination_location_label = loc.name or loc.code or str(destination_location)
        else:
            destination_location_label = str(destination_location)

    return ItemLocationOut(
        item_key=str(part_id),
        found=True,
        part_db_id=part_id,
        last_movement_id=str(movement_id) if movement_id is not None else None,
        movement_type=str(movement_type) if movement_type is not None else None,
        source_location=int(source_location) if source_location not in (None, "") else None,
        destination_location=int(destination_location) if destination_location not in (None, "") else None,
        destination_location_label=destination_location_label,
        done_by=int(done_by) if done_by not in (None, "") else None,
        movement_date=str(movement_date) if movement_date is not None else None,
        raw=last_mv,
    )