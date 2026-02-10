from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_, select

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import StockContainer, Item, Location
from warehouse18.presentation.api.schemas import StockContainerCreateIn, StockContainerOut, StockContainerUpdateIn, PageOut

from warehouse18.presentation.api.paging import paginate

router = APIRouter(prefix="/stock-containers", tags=["stock_containers"])

@router.post("/", response_model=StockContainerOut)
def create_stock_container(body: StockContainerCreateIn, db: Session = Depends(get_db)):
    # validar item existe y NO serializado
    it = db.query(Item).filter(Item.id == body.item_id).first()
    if not it:
        raise HTTPException(status_code=409, detail="Item not found")
    if it.is_serialized:
        raise HTTPException(status_code=409, detail="Cannot create stock container for serialized item")

    # validar location existe
    loc = db.query(Location).filter(Location.id == body.location_id).first()
    if not loc:
        raise HTTPException(status_code=409, detail="Location not found")

    if body.container_code:
        exists = db.query(StockContainer).filter(StockContainer.container_code == body.container_code).first()
        if exists:
            raise HTTPException(status_code=409, detail="container_code already exists")

    try:
        sc = StockContainer(**body.model_dump())
        db.add(sc)
        db.commit()
        db.refresh(sc)
        return sc
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))

@router.get("/", response_model=PageOut[StockContainerOut])
def list_stock_containers(
    db: Session = Depends(get_db),
    q: str | None = None,
    item_id: int | None = None,
    location_id: int | None = None,
    include_inactive: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    stmt = select(StockContainer)

    if not include_inactive:
        stmt = stmt.where(StockContainer.is_active.is_(True))

    if item_id is not None:
        stmt = stmt.where(StockContainer.item_id == item_id)

    if location_id is not None:
        stmt = stmt.where(StockContainer.location_id == location_id)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                StockContainer.container_code.ilike(like),
            )
        )

    stmt = stmt.order_by(StockContainer.id.asc())

    items, total, pages = paginate(db, stmt, page=page, page_size=page_size)

    return PageOut[StockContainerOut](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

@router.get("/{container_id}", response_model=StockContainerOut)
def get_stock_container(container_id: int, db: Session = Depends(get_db)):
    sc = db.query(StockContainer).filter(StockContainer.id == container_id).first()
    if not sc:
        raise HTTPException(status_code=409, detail="Stock container not found")
    return sc

@router.patch("/{container_id}", response_model=StockContainerOut)
def update_stock_container(container_id: int, body: StockContainerUpdateIn, db: Session = Depends(get_db)):
    sc = db.query(StockContainer).filter(StockContainer.id == container_id).first()
    if not sc:
        raise HTTPException(status_code=409, detail="Stock container not found")

    data = body.model_dump(exclude_unset=True)

    if "location_id" in data and data["location_id"] is not None:
        loc = db.query(Location).filter(Location.id == data["location_id"]).first()
        if not loc:
            raise HTTPException(status_code=409, detail="Location not found")

    if "container_code" in data and data["container_code"]:
        exists = db.query(StockContainer).filter(
            StockContainer.container_code == data["container_code"],
            StockContainer.id != container_id
        ).first()
        if exists:
            raise HTTPException(status_code=409, detail="container_code already exists")

    try:
        for k, v in data.items():
            setattr(sc, k, v)

        db.commit()
        db.refresh(sc)
        return sc
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))

@router.delete("/{container_id}")
def delete_stock_container(container_id: int, db: Session = Depends(get_db)):
    sc = db.query(StockContainer).filter(StockContainer.id == container_id).first()
    if not sc:
        raise HTTPException(status_code=409, detail="Stock container not found")

    sc.is_active = False
    try:
        db.commit()
        return {"status": "ok"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))