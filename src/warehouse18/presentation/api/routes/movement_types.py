from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import MovementType
from warehouse18.presentation.api.schemas import MovementTypeOut

router = APIRouter(prefix="/movement-types", tags=["movement_types"])

@router.get("/", response_model=list[MovementTypeOut])
def list_movement_types(db: Session = Depends(get_db)):
    return db.query(MovementType).order_by(MovementType.code.asc()).all()
