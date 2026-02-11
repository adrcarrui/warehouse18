from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import Asset, AssetLocation, Item, Location
from warehouse18.presentation.api.schemas import AssetCreateIn, AssetUpdateIn, AssetOut, PageOut

from warehouse18.presentation.api.paging import paginate
from warehouse18.presentation.api.pagination_headers import set_pagination_headers

router = APIRouter(prefix="/assets", tags=["assets"])

VALID_STATUSES = {"active", "repair", "scrapped", "lost", "inactive"}


def _to_out(a: Asset) -> AssetOut:
    loc_id = a.location.location_id if a.location else None
    loc_since = a.location.since if a.location else None
    return AssetOut(
        id=a.id,
        asset_code=a.asset_code,
        item_id=a.item_id,
        status=a.status,
        created_at=a.created_at,
        updated_at=a.updated_at,
        location_id=loc_id,
        location_since=loc_since,
    )


@router.post("/", response_model=AssetOut)
def create_asset(body: AssetCreateIn, db: Session = Depends(get_db)):
    # 1) item_id obligatorio para crear asset (tu modelo lo requiere de facto)
    if body.item_id is None:
        raise HTTPException(status_code=409, detail="item_id is required")

    it = db.query(Item).filter(Item.id == body.item_id).first()
    if not it:
        raise HTTPException(status_code=409, detail="Item not found")
    if not it.is_serialized:
        raise HTTPException(status_code=409, detail=f"Item {body.item_id} is not serialized")

    # 2) status válido
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=409, detail="Invalid status")

    # 3) asset_code único
    if db.query(Asset).filter(Asset.asset_code == body.asset_code).first():
        raise HTTPException(status_code=409, detail="asset_code already exists")

    # 4) location_id existe (si viene)
    if body.location_id is not None:
        loc = db.query(Location).filter(Location.id == body.location_id).first()
        if not loc:
            raise HTTPException(status_code=409, detail="Location not found")

    try:
        a = Asset(
            asset_code=body.asset_code,
            item_id=body.item_id,
            status=body.status,
        )
        db.add(a)
        db.flush()  # a.id disponible

        if body.location_id is not None:
            db.add(AssetLocation(asset_id=a.id, location_id=body.location_id))

        db.commit()
        db.refresh(a)
        return _to_out(a)

    except IntegrityError as e:
        db.rollback()
        # tu app ya mapea DBAPIError/IntegrityError a 409,
        # pero aquí devolvemos 409 directo por consistencia y para no romper la sesión
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.get("/", response_model=PageOut[AssetOut])
def list_assets(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    q: str | None = Query(None, max_length=200),
    item_id: int | None = None,
    status: str | None = None,
    location_id: int | None = None,
    include_inactive: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    # Usamos select() y join a AssetLocation (ubicación actual) para poder filtrar por location_id
    # y además evitar el N+1 cuando luego hacemos _to_out(a) leyendo a.location
    stmt = select(Asset).outerjoin(AssetLocation, AssetLocation.asset_id == Asset.id)

    if item_id is not None:
        stmt = stmt.where(Asset.item_id == item_id)

    if status is not None:
        stmt = stmt.where(Asset.status == status)

    # Si quieres tratar "inactive" como soft-delete:
    if not include_inactive:
        stmt = stmt.where(Asset.status != "inactive")

    if location_id is not None:
        stmt = stmt.where(AssetLocation.location_id == location_id)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Asset.asset_code.ilike(like),
            )
        )

    # Orden estable para paginación
    stmt = stmt.order_by(Asset.id.asc())

    assets, total, pages = paginate(db, stmt, page=page, page_size=page_size)

    # Headers útiles de paginación
    set_pagination_headers(
        request=request,
        response=response,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

    # Convertimos a AssetOut porque lleva location_id/location_since derivados
    out_items = [_to_out(a) for a in assets]

    return PageOut[AssetOut](
        items=out_items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    a = db.query(Asset).filter(Asset.id == asset_id).first()
    if not a:
        raise HTTPException(status_code=409, detail="Asset not found")
    return _to_out(a)


@router.get("/by-code/{asset_code}", response_model=AssetOut)
def get_asset_by_code(asset_code: str, db: Session = Depends(get_db)):
    a = db.query(Asset).filter(Asset.asset_code == asset_code).first()
    if not a:
        raise HTTPException(status_code=409, detail="Asset not found")
    return _to_out(a)


@router.patch("/{asset_id}", response_model=AssetOut)
def update_asset(asset_id: int, body: AssetUpdateIn, db: Session = Depends(get_db)):
    a = db.query(Asset).filter(Asset.id == asset_id).first()
    if not a:
        raise HTTPException(status_code=409, detail="Asset not found")

    data = body.model_dump(exclude_unset=True)

    if "status" in data and data["status"] is not None:
        if data["status"] not in VALID_STATUSES:
            raise HTTPException(status_code=409, detail="Invalid status")
        a.status = data["status"]

    if "item_id" in data:
        a.item_id = data["item_id"]

    # cambiar ubicación actual (sin SP) si quieres permitirlo aquí
    if "location_id" in data:
        loc_id = data["location_id"]
        if loc_id is None:
            # si quieres permitir "quitar ubicación", tendrías que borrar asset_location
            # yo lo dejo como no permitido (mínimo funcional)
            raise HTTPException(status_code=409, detail="location_id cannot be null")
        if a.location:
            a.location.location_id = loc_id
            a.location.since = func.now()
        else:
            db.add(AssetLocation(asset_id=a.id, location_id=loc_id))

    try:
        db.commit()
        db.refresh(a)
        return _to_out(a)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    a = db.query(Asset).filter(Asset.id == asset_id).first()
    if not a:
        raise HTTPException(status_code=409, detail="Asset not found")

    # “soft delete” usando status, porque tu tabla no tiene is_active
    a.status = "inactive"
    try:
        db.commit()
        return {"status": "ok"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))
