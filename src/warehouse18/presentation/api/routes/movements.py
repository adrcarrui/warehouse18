from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import Movement, MovementType, Item, Location, User
from warehouse18.presentation.api.schemas import MovementCreateIn, MovementOut

router = APIRouter(prefix="/movements", tags=["movements"])

VALID_REF_TYPES = {"asset", "container"}

@router.post("/", response_model=MovementOut)
def create_movement(body: MovementCreateIn, db: Session = Depends(get_db)):
    mt = db.query(MovementType).filter(MovementType.id == body.movement_type_id).first()
    if not mt:
        raise HTTPException(status_code=409, detail="movement_type not found")

    # Validación mínima coherente con tus flags
    if mt.affects_stock:
        if body.item_id is None:
            raise HTTPException(status_code=409, detail="item_id is required for stock-affecting movement")
        if body.quantity is None:
            raise HTTPException(status_code=409, detail="quantity is required for stock-affecting movement")

        it = db.query(Item).filter(Item.id == body.item_id).first()
        if not it:
            raise HTTPException(status_code=409, detail="Item not found")

    if mt.affects_location:
        # Para movimientos de ubicación normalmente necesitas al menos un lado
        if body.from_location_id is None and body.to_location_id is None:
            raise HTTPException(status_code=409, detail="from_location_id or to_location_id is required for location-affecting movement")

        if body.from_location_id is not None:
            if not db.query(Location).filter(Location.id == body.from_location_id).first():
                raise HTTPException(status_code=409, detail="from_location not found")
        if body.to_location_id is not None:
            if not db.query(Location).filter(Location.id == body.to_location_id).first():
                raise HTTPException(status_code=409, detail="to_location not found")

    # reference pair: ambos o ninguno (tu CHECK lo exige)
    if (body.reference_type is None) != (body.reference_id is None):
        raise HTTPException(status_code=409, detail="reference_type and reference_id must be provided together")

    if body.reference_type is not None and body.reference_type not in VALID_REF_TYPES:
        raise HTTPException(status_code=409, detail="Invalid reference_type")

    # user opcional, pero si viene, valida
    if body.user_id is not None:
        if not db.query(User).filter(User.id == body.user_id).first():
            raise HTTPException(status_code=409, detail="User not found")

    try:
        mv = Movement(**body.model_dump())
        db.add(mv)
        db.commit()
        db.refresh(mv)
        return mv
    except IntegrityError as e:
        db.rollback()
        # tu regla: todo 409
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.get("/", response_model=list[MovementOut])
def list_movements(
    db: Session = Depends(get_db),
    movement_type_id: int | None = None,
    item_id: int | None = None,
    from_location_id: int | None = None,
    to_location_id: int | None = None,
    user_id: int | None = None,
):
    q = db.query(Movement).order_by(Movement.created_at.desc())
    if movement_type_id is not None:
        q = q.filter(Movement.movement_type_id == movement_type_id)
    if item_id is not None:
        q = q.filter(Movement.item_id == item_id)
    if from_location_id is not None:
        q = q.filter(Movement.from_location_id == from_location_id)
    if to_location_id is not None:
        q = q.filter(Movement.to_location_id == to_location_id)
    if user_id is not None:
        q = q.filter(Movement.user_id == user_id)
    return q.all()


@router.get("/{movement_id}", response_model=MovementOut)
def get_movement(movement_id: int, db: Session = Depends(get_db)):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()
    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")
    return mv
