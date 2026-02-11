from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, select

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import InventoryStock
from warehouse18.presentation.api.schemas import InventoryStockOut, PageOut

from warehouse18.presentation.api.paging import paginate
from warehouse18.presentation.api.pagination_headers import set_pagination_headers

router = APIRouter(prefix="/inventory-stock", tags=["inventory_stock"])

@router.get("/", response_model=PageOut[InventoryStockOut])
def list_inventory_stock(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    item_id: int | None = None,
    location_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    stmt = select(InventoryStock)

    if item_id is not None:
        stmt = stmt.where(InventoryStock.item_id == item_id)

    if location_id is not None:
        stmt = stmt.where(InventoryStock.location_id == location_id)

    stmt = stmt.order_by(InventoryStock.item_id.asc(), InventoryStock.location_id.asc())

    items, total, pages = paginate(db, stmt, page=page, page_size=page_size)

    set_pagination_headers(
        request=request,
        response=response,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

    return PageOut[InventoryStockOut](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/by-item/{item_id}", response_model=PageOut[InventoryStockOut])
def list_inventory_stock_by_item(
    item_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    stmt = (
        select(InventoryStock)
        .where(InventoryStock.item_id == item_id)
        .order_by(InventoryStock.location_id.asc())
    )

    items, total, pages = paginate(db, stmt, page=page, page_size=page_size)

    set_pagination_headers(
        request=request,
        response=response,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

    return PageOut[InventoryStockOut](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/by-location/{location_id}", response_model=PageOut[InventoryStockOut])
def list_inventory_stock_by_location(
    location_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    stmt = (
        select(InventoryStock)
        .where(InventoryStock.location_id == location_id)
        .order_by(InventoryStock.item_id.asc())
    )

    items, total, pages = paginate(db, stmt, page=page, page_size=page_size)

    set_pagination_headers(
        request=request,
        response=response,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

    return PageOut[InventoryStockOut](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )