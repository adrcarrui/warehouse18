from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import Item
from warehouse18.presentation.api.schemas import ItemCreateIn, ItemUpdateIn, ItemOut, PageOut

from sqlalchemy import or_, select
from warehouse18.presentation.api.paging import paginate
from warehouse18.presentation.api.pagination_headers import set_pagination_headers

router = APIRouter(prefix="/items", tags=["items"])


def _norm_code(code: str | None) -> str | None:
    """Normaliza item_code: recorta y convierte '' en None."""
    if code is None:
        return None
    code = code.strip()
    return code or None


def _validate_stock_levels(min_stock, reorder_point):
    # Deja que DB sea la autoridad, pero así evitamos 500 tontos.
    if min_stock is not None and min_stock < 0:
        raise HTTPException(status_code=409, detail="min_stock must be >= 0")
    if reorder_point is not None and reorder_point < 0:
        raise HTTPException(status_code=409, detail="reorder_point must be >= 0")
    if min_stock is not None and reorder_point is not None and reorder_point < min_stock:
        raise HTTPException(status_code=409, detail="reorder_point must be >= min_stock")


@router.post("/", response_model=ItemOut)
def create_item(body: ItemCreateIn, db: Session = Depends(get_db)):
    code = _norm_code(body.item_code)
    _validate_stock_levels(body.min_stock, body.reorder_point)

    # item_code UNIQUE si no es null (en DB está como índice único parcial)
    if code is not None:
        exists = db.query(Item).filter(Item.item_code == code).first()
        if exists:
            raise HTTPException(status_code=409, detail="item_code already exists")

    try:
        payload = body.model_dump()
        payload["item_code"] = code

        it = Item(**payload)
        db.add(it)
        db.commit()
        db.refresh(it)
        return it

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.get("/", response_model=PageOut[ItemOut])
def list_items(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    include_inactive: bool = False,
    q: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    stmt = select(Item)

    if not include_inactive:
        stmt = stmt.where(Item.is_active.is_(True))

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Item.item_code.ilike(like),
                Item.name.ilike(like),
                Item.description.ilike(like),
                Item.category.ilike(like),
                Item.uom.ilike(like),
            )
        )

    # Orden estable (importantísimo para paginación)
    stmt = stmt.order_by(Item.id.asc())

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

    return PageOut[ItemOut](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

@router.get("/{item_id}", response_model=ItemOut)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    include_inactive: bool = False,
):
    q = db.query(Item).filter(Item.id == item_id)
    if not include_inactive:
        q = q.filter(Item.is_active.is_(True))

    it = q.first()
    if not it:
        raise HTTPException(status_code=409, detail="Item not found")
    return it


@router.patch("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, body: ItemUpdateIn, db: Session = Depends(get_db)):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it:
        raise HTTPException(status_code=409, detail="Item not found")

    data = body.model_dump(exclude_unset=True)

    # Normaliza item_code si viene en el PATCH (permite "borrar" mandando "")
    if "item_code" in data:
        data["item_code"] = _norm_code(data["item_code"])

    # Validación stock levels si tocan alguno de los dos
    min_stock = data.get("min_stock", it.min_stock)
    reorder_point = data.get("reorder_point", it.reorder_point)
    _validate_stock_levels(min_stock, reorder_point)

    # Si cambian item_code, validar unique cuando no sea null
    if "item_code" in data and data["item_code"] is not None:
        exists = (
            db.query(Item)
            .filter(Item.item_code == data["item_code"], Item.id != item_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=409, detail="item_code already exists")

    try:
        for k, v in data.items():
            setattr(it, k, v)

        db.commit()
        db.refresh(it)
        return it

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it:
        raise HTTPException(status_code=409, detail="Item not found")

    it.is_active = False
    db.commit()
    return {"status": "ok"}
