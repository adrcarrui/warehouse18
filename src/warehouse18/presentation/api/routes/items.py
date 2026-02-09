from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import Item
from warehouse18.presentation.api.schemas import ItemCreateIn, ItemUpdateIn, ItemOut

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=ItemOut)
def create_item(body: ItemCreateIn, db: Session = Depends(get_db)):
    # item_code es UNIQUE si no es null
    if body.item_code:
        exists = db.query(Item).filter(Item.item_code == body.item_code).first()
        if exists:
            raise HTTPException(status_code=409, detail="item_code already exists")

    it = Item(**body.model_dump())
    db.add(it)
    db.commit()
    db.refresh(it)
    return it


@router.get("/", response_model=list[ItemOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).order_by(Item.id.asc()).all()


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it:
        raise HTTPException(status_code=409, detail="Item not found")
    return it


@router.patch("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, body: ItemUpdateIn, db: Session = Depends(get_db)):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it:
        raise HTTPException(status_code=409, detail="Item not found")

    data = body.model_dump(exclude_unset=True)

    # Si cambian item_code, validar unique cuando no sea null/vacio
    if "item_code" in data and data["item_code"]:
        exists = db.query(Item).filter(Item.item_code == data["item_code"], Item.id != item_id).first()
        if exists:
            raise HTTPException(status_code=409, detail="item_code already exists")

    # Aplicar cambios
    for k, v in data.items():
        setattr(it, k, v)

    db.commit()
    db.refresh(it)
    return it


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    it = db.query(Item).filter(Item.id == item_id).first()
    if not it:
        raise HTTPException(status_code=409, detail="Item not found")

    # soft delete
    it.is_active = False
    db.commit()
    return {"status": "ok"}
