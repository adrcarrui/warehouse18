from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import Location
from warehouse18.presentation.api.schemas import LocationCreateIn, LocationUpdateIn, LocationOut

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("/", response_model=LocationOut)
def create_location(body: LocationCreateIn, db: Session = Depends(get_db)):
    if db.query(Location).filter(Location.code == body.code).first():
        raise HTTPException(status_code=409, detail="Location already exists")

    # si parent_id viene informado, valida que exista
    if body.parent_id is not None:
        parent = db.query(Location).filter(Location.id == body.parent_id).first()
        if not parent:
            raise HTTPException(status_code=409, detail="Parent location not found")

    loc = Location(**body.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.get("/", response_model=list[LocationOut])
def list_locations(db: Session = Depends(get_db)):
    return db.query(Location).order_by(Location.code.asc()).all()


@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=409, detail="Location not found")
    return loc


@router.patch("/{location_id}", response_model=LocationOut)
def update_location(location_id: int, body: LocationUpdateIn, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=409, detail="Location not found")

    data = body.model_dump(exclude_unset=True)

    # Si cambian parent_id, valida existencia (y permite null para “quitar padre”)
    if "parent_id" in data and data["parent_id"] is not None:
        parent = db.query(Location).filter(Location.id == data["parent_id"]).first()
        if not parent:
            raise HTTPException(status_code=409, detail="Parent location not found")

        # evita ciclos tontos: parent_id == self
        if data["parent_id"] == location_id:
            raise HTTPException(status_code=409, detail="parent_id cannot be the same location")

    for k, v in data.items():
        setattr(loc, k, v)

    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=409, detail="Location not found")

    # soft delete
    loc.is_active = False
    db.commit()
    return {"status": "ok"}
