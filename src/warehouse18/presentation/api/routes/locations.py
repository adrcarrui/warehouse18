from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import Location
from warehouse18.presentation.api.schemas import LocationCreateIn, LocationUpdateIn, LocationOut, PageOut
from sqlalchemy.exc import IntegrityError

from warehouse18.presentation.api.paging import paginate
from warehouse18.presentation.api.pagination_headers import set_pagination_headers

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
    try:
        db.commit()
        db.refresh(loc)
        return loc
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.get("/", response_model=PageOut[LocationOut])
def list_locations(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    q: str | None = Query(None, max_length=200),
    parent_id: int | None = None,
    include_inactive: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    stmt = select(Location)

    if not include_inactive:
        stmt = stmt.where(Location.is_active.is_(True))

    if parent_id is not None:
        stmt = stmt.where(Location.parent_id == parent_id)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Location.code.ilike(like),
                Location.name.ilike(like),
            )
        )

    # Orden estable para paginación
    stmt = stmt.order_by(Location.code.asc())

    items, total, pages = paginate(db, stmt, page=page, page_size=page_size)

    # Headers útiles
    set_pagination_headers(
        request=request,
        response=response,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

    return PageOut[LocationOut](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


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

    try:
        db.commit()
        db.refresh(loc)
        return loc
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=409, detail="Location not found")

    # soft delete
    loc.is_active = False
    try:
        db.commit()
        return {"status": "ok"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))
