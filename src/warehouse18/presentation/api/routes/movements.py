from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, select
from datetime import datetime, timezone

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import Movement, MovementType, Item, Location, User
from warehouse18.presentation.api.schemas import (
    MovementCreateIn,
    MovementOut,
    MovementConfirmIn,
    MovementRejectIn,
    MovementLocationsUpdateIn,
    PageOut,
)
from warehouse18.presentation.api.paging import paginate
from warehouse18.presentation.api.pagination_headers import set_pagination_headers

router = APIRouter(prefix="/movements", tags=["movements"])

VALID_REF_TYPES = {"asset", "container"}

REVIEW_STATUS_PENDING = "pending"
REVIEW_STATUS_CONFIRMED = "confirmed"
REVIEW_STATUS_REJECTED = "rejected"

MYSIM_SYNC_STATUS_PENDING_REVIEW = "pending_review"
MYSIM_SYNC_STATUS_QUEUED = "queued"
MYSIM_SYNC_STATUS_NOT_SENT = "not_sent"


def _movement_type_name(db: Session, movement_type_id: int) -> str | None:
    mt = db.query(MovementType).filter(MovementType.id == movement_type_id).first()
    if not mt:
        return None
    return mt.name


def _compute_report_reason_for_confirmation(mv: Movement, movement_type_name: str | None) -> str | None:
    missing_user = mv.user_id is None

    # Regla de negocio:
    # - Goods Receipt: reportar si falta destino o user
    # - Goods Transfer: reportar si falta destino o user
    # - Goods Issue: reportar si falta user
    #   (si quieres forzar también destino para GI, se cambia aquí y listo)
    missing_destination = False
    if movement_type_name in {"Goods Receipt", "Goods Transfer"}:
        missing_destination = mv.to_location_id is None

    if missing_user and missing_destination:
        return "missing_user_and_destination"
    if missing_user:
        return "missing_user"
    if missing_destination:
        return "missing_destination"
    return None


@router.post("/", response_model=MovementOut)
def create_movement(body: MovementCreateIn, db: Session = Depends(get_db)):
    mt = db.query(MovementType).filter(MovementType.id == body.movement_type_id).first()
    if not mt:
        raise HTTPException(status_code=409, detail="movement_type not found")

    if mt.affects_stock:
        if body.item_id is None:
            raise HTTPException(status_code=409, detail="item_id is required for stock-affecting movement")
        if body.quantity is None:
            raise HTTPException(status_code=409, detail="quantity is required for stock-affecting movement")

        it = db.query(Item).filter(Item.id == body.item_id).first()
        if not it:
            raise HTTPException(status_code=409, detail="Item not found")

    if mt.affects_location:
        if body.from_location_id is None and body.to_location_id is None:
            raise HTTPException(status_code=409, detail="from_location_id or to_location_id is required for location-affecting movement")

        if body.from_location_id is not None:
            if not db.query(Location).filter(Location.id == body.from_location_id).first():
                raise HTTPException(status_code=409, detail="from_location not found")
        if body.to_location_id is not None:
            if not db.query(Location).filter(Location.id == body.to_location_id).first():
                raise HTTPException(status_code=409, detail="to_location not found")

    if (body.reference_type is None) != (body.reference_id is None):
        raise HTTPException(status_code=409, detail="reference_type and reference_id must be provided together")

    if body.reference_type is not None and body.reference_type not in VALID_REF_TYPES:
        raise HTTPException(status_code=409, detail="Invalid reference_type")

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
        raise HTTPException(status_code=409, detail=str(e.orig))


@router.get("/", response_model=PageOut[MovementOut])
def list_movements(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    q: str | None = Query(None, max_length=200),
    movement_type_id: int | None = None,
    item_id: int | None = None,
    from_location_id: int | None = None,
    to_location_id: int | None = None,
    user_id: int | None = None,
    reference_type: str | None = Query(None, max_length=50),
    reference_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    review_status: str | None = Query(None, max_length=20),
    needs_report: bool | None = None,
    is_preventive: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    stmt = select(Movement)

    if movement_type_id is not None:
        stmt = stmt.where(Movement.movement_type_id == movement_type_id)
    if item_id is not None:
        stmt = stmt.where(Movement.item_id == item_id)
    if from_location_id is not None:
        stmt = stmt.where(Movement.from_location_id == from_location_id)
    if to_location_id is not None:
        stmt = stmt.where(Movement.to_location_id == to_location_id)
    if user_id is not None:
        stmt = stmt.where(Movement.user_id == user_id)

    if reference_type is not None:
        stmt = stmt.where(Movement.reference_type == reference_type)
    if reference_id is not None:
        stmt = stmt.where(Movement.reference_id == reference_id)

    if from_date is not None:
        stmt = stmt.where(Movement.created_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(Movement.created_at <= to_date)

    if review_status is not None:
        stmt = stmt.where(Movement.review_status == review_status)

    if needs_report is not None:
        stmt = stmt.where(Movement.needs_report == needs_report)

    if is_preventive is not None:
        stmt = stmt.where(Movement.is_preventive == is_preventive)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Movement.notes.ilike(like),
                Movement.reference_type.ilike(like),
                Movement.item_key.ilike(like),
                Movement.report_reason.ilike(like),
            )
        )

    stmt = stmt.order_by(Movement.created_at.desc())

    items, total, pages = paginate(db, stmt, page=page, page_size=page_size)

    set_pagination_headers(
        request=request,
        response=response,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

    return PageOut[MovementOut](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/{movement_id}", response_model=MovementOut)
def get_movement(movement_id: int, db: Session = Depends(get_db)):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()
    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")
    return mv


@router.post("/{movement_id}/confirm", response_model=MovementOut)
def confirm_movement(
    movement_id: int,
    body: MovementConfirmIn,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()
    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    if mv.review_status == REVIEW_STATUS_CONFIRMED:
        return mv

    if mv.review_status == REVIEW_STATUS_REJECTED:
        raise HTTPException(status_code=409, detail="Movement already rejected")

    if body.reviewed_by_user_id is not None:
        reviewer = db.query(User).filter(User.id == body.reviewed_by_user_id).first()
        if not reviewer:
            raise HTTPException(status_code=409, detail="Reviewer user not found")

    movement_type_name = _movement_type_name(db, mv.movement_type_id)
    if movement_type_name is None:
        raise HTTPException(status_code=409, detail="movement_type not found")

    reason = _compute_report_reason_for_confirmation(mv, movement_type_name)

    mv.review_status = REVIEW_STATUS_CONFIRMED
    mv.reviewed_at = datetime.now(timezone.utc)
    mv.reviewed_by_user_id = body.reviewed_by_user_id
    mv.review_note = body.review_note

    mv.needs_report = reason is not None
    mv.report_reason = reason

    # Solo se cola para sync cuando se confirma.
    # Si prefieres bloquear sync cuando needs_report=True, se cambia aquí.
    mv.mysim_sync_status = MYSIM_SYNC_STATUS_QUEUED

    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv


@router.post("/{movement_id}/reject", response_model=MovementOut)
def reject_movement(
    movement_id: int,
    body: MovementRejectIn,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()
    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    if mv.review_status == REVIEW_STATUS_REJECTED:
        return mv

    if mv.review_status == REVIEW_STATUS_CONFIRMED:
        raise HTTPException(status_code=409, detail="Movement already confirmed")

    if body.reviewed_by_user_id is not None:
        reviewer = db.query(User).filter(User.id == body.reviewed_by_user_id).first()
        if not reviewer:
            raise HTTPException(status_code=409, detail="Reviewer user not found")

    mv.review_status = REVIEW_STATUS_REJECTED
    mv.reviewed_at = datetime.now(timezone.utc)
    mv.reviewed_by_user_id = body.reviewed_by_user_id
    mv.review_note = body.review_note

    mv.mysim_sync_status = MYSIM_SYNC_STATUS_NOT_SENT

    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv

@router.patch("/{movement_id}/locations", response_model=MovementOut)
def update_movement_locations(
    movement_id: int,
    body: MovementLocationsUpdateIn,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()
    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    if body.from_location_id is not None:
        from_loc = db.query(Location).filter(Location.id == body.from_location_id).first()
        if not from_loc:
            raise HTTPException(status_code=409, detail="from_location not found")
        mv.from_location_id = body.from_location_id

    if body.to_location_id is not None:
        to_loc = db.query(Location).filter(Location.id == body.to_location_id).first()
        if not to_loc:
            raise HTTPException(status_code=409, detail="to_location not found")
        mv.to_location_id = body.to_location_id

    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv