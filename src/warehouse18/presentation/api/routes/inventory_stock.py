from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import InventoryStock
from warehouse18.presentation.api.schemas import InventoryStockOut

router = APIRouter(prefix="/inventory-stock", tags=["inventory_stock"])

@router.get("/", response_model=list[InventoryStockOut])
def list_inventory_stock(db: Session = Depends(get_db)):
    return (
        db.query(InventoryStock)
        .order_by(InventoryStock.item_id.asc(), InventoryStock.location_id.asc())
        .all()
    )

@router.get("/by-item/{item_id}", response_model=list[InventoryStockOut])
def list_inventory_stock_by_item(item_id: int, db: Session = Depends(get_db)):
    return db.query(InventoryStock).filter(InventoryStock.item_id == item_id).all()

@router.get("/by-location/{location_id}", response_model=list[InventoryStockOut])
def list_inventory_stock_by_location(location_id: int, db: Session = Depends(get_db)):
    return db.query(InventoryStock).filter(InventoryStock.location_id == location_id).all()
