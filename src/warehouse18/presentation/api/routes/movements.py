from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from warehouse18.application.rfid.event_log_service import log_rfid_event
from warehouse18.domain.models import Item, Location, Movement, MovementType, User
from warehouse18.domain.models.rfid_event_log import RfidEventLog
from warehouse18.infrastructure.db import get_db
from warehouse18.presentation.api.pagination_headers import set_pagination_headers
from warehouse18.presentation.api.paging import paginate
from warehouse18.presentation.api.schemas import (
    MovementCreateIn,
    MovementOut,
    MovementReviewIn,
    MovementReviewOut,
    MovementLocationsUpdateIn,
    MovementQuantityUpdateIn,
    PageOut,
)
from warehouse18.application.integrations.outbox_service import enqueue_movement_sync

router = APIRouter(prefix="/movements", tags=["movements"])

VALID_REF_TYPES = {"asset", "container"}


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
    review_status: str | None = None,
    mysim_sync_status: str | None = None,
    reference_type: str | None = Query(None, max_length=50),
    reference_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    stmt = select(Movement).options(joinedload(Movement.user))

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
    if review_status is not None:
        stmt = stmt.where(Movement.review_status == review_status)
    if mysim_sync_status is not None:
        stmt = stmt.where(Movement.mysim_sync_status == mysim_sync_status)
    if reference_type is not None:
        stmt = stmt.where(Movement.reference_type == reference_type)
    if reference_id is not None:
        stmt = stmt.where(Movement.reference_id == reference_id)
    if from_date is not None:
        stmt = stmt.where(Movement.created_at >= from_date)
    if to_date is not None:
        stmt = stmt.where(Movement.created_at <= to_date)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Movement.notes.ilike(like),
                Movement.reference_type.ilike(like),
                Movement.item_key.ilike(like),
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

    items_out = [
        MovementOut(
            id=m.id,
            movement_type_id=m.movement_type_id,
            item_id=m.item_id,
            quantity=m.quantity,
            from_location_id=m.from_location_id,
            to_location_id=m.to_location_id,
            reference_type=m.reference_type,
            reference_id=m.reference_id,
            mysim_user_id=m.mysim_user_id,
            user_id=m.user_id,
            user_name=m.user.username if getattr(m, "user", None) else None,
            created_at=m.created_at,
            notes=m.notes,
            item_key=m.item_key,
            review_status=m.review_status,
            reviewed_at=m.reviewed_at,
            reviewed_by_user_id=m.reviewed_by_user_id,
            review_note=m.review_note,
            mysim_sync_status=m.mysim_sync_status,
            mysim_synced_at=m.mysim_synced_at,
            mysim_sync_error=m.mysim_sync_error,
            mysim_movement_id=m.mysim_movement_id,
        )
        for m in items
    ]

    return PageOut[MovementOut](
        items=items_out,
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


@router.post("/{movement_id}/confirm", response_model=MovementReviewOut)
def confirm_movement_review(
    movement_id: int,
    body: MovementReviewIn,
    db: Session = Depends(get_db),
):
    reviewer = db.query(User).filter(User.id == body.reviewed_by_user_id).first()
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer user not found")

    movement = (
        db.query(Movement)
        .filter(Movement.id == movement_id)
        .with_for_update()
        .first()
    )
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")

    # Si ya estaba confirmado y sincronizado, no reenviar otra vez
    if movement.review_status == "confirmed" and movement.mysim_sync_status == "ok":
        return MovementReviewOut(
            movement_id=movement.id,
            review_status=movement.review_status,
            reviewed_at=movement.reviewed_at,
            reviewed_by_user_id=movement.reviewed_by_user_id,
            mysim_sync_status=movement.mysim_sync_status,
            mysim_sync_error=movement.mysim_sync_error,
            mysim_movement_id=movement.mysim_movement_id,
        )

    # Si ya está en cola o en proceso, no dejar otra confirmación simultánea
    if movement.mysim_sync_status in {"queued", "syncing"}:
        raise HTTPException(status_code=409, detail="Movement sync already queued or in progress")

    # Confirm must only happen once, from pending state
    if movement.review_status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Only pending movements can be confirmed (current status={movement.review_status})",
        )

    now = datetime.now(timezone.utc)

    movement.review_status = "confirmed"
    movement.reviewed_at = now
    movement.reviewed_by_user_id = body.reviewed_by_user_id
    movement.review_note = body.note
    movement.mysim_sync_status = "queued"
    movement.mysim_sync_error = None

    db.add(movement)
    db.flush()

    enqueue_movement_sync(
        db,
        movement_id=movement.id,
        trigger="manual_confirm",
    )

    db.query(RfidEventLog).filter(RfidEventLog.movement_id == movement_id).update(
        {
            RfidEventLog.review_status: "confirmed",
            RfidEventLog.reviewed_at: now,
            RfidEventLog.reviewed_by_user_id: body.reviewed_by_user_id,
            RfidEventLog.review_note: body.note,
            RfidEventLog.confirmed_movement_id: movement.id,
        },
        synchronize_session=False,
    )

    db.commit()
    db.refresh(movement)

    return MovementReviewOut(
        movement_id=movement.id,
        review_status=movement.review_status,
        reviewed_at=movement.reviewed_at,
        reviewed_by_user_id=movement.reviewed_by_user_id,
        mysim_sync_status=movement.mysim_sync_status,
        mysim_sync_error=movement.mysim_sync_error,
        mysim_movement_id=movement.mysim_movement_id,
    )


@router.post("/{movement_id}/reject", response_model=MovementReviewOut)
def reject_movement_review(
    movement_id: int,
    body: MovementReviewIn,
    db: Session = Depends(get_db),
):
    reviewer = db.query(User).filter(User.id == body.reviewed_by_user_id).first()
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer user not found")

    movement = (
        db.query(Movement)
        .filter(Movement.id == movement_id)
        .with_for_update()
        .first()
    )
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")

    if movement.review_status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Only pending movements can be rejected (current status={movement.review_status})",
        )

    now = datetime.now(timezone.utc)

    movement.review_status = "rejected"
    movement.reviewed_at = now
    movement.reviewed_by_user_id = body.reviewed_by_user_id
    movement.review_note = body.note
    movement.mysim_sync_status = "skipped"
    movement.mysim_sync_error = None

    db.add(movement)
    db.flush()

    db.query(RfidEventLog).filter(RfidEventLog.movement_id == movement_id).update(
        {
            RfidEventLog.review_status: "rejected",
            RfidEventLog.reviewed_at: now,
            RfidEventLog.reviewed_by_user_id: body.reviewed_by_user_id,
            RfidEventLog.review_note: body.note,
            RfidEventLog.confirmed_movement_id: None,
        },
        synchronize_session=False,
    )

    db.commit()
    db.refresh(movement)

    return MovementReviewOut(
        movement_id=movement.id,
        review_status=movement.review_status,
        reviewed_at=movement.reviewed_at,
        reviewed_by_user_id=movement.reviewed_by_user_id,
        mysim_sync_status=movement.mysim_sync_status,
        mysim_sync_error=movement.mysim_sync_error,
        mysim_movement_id=movement.mysim_movement_id,
    )

@router.patch("/{movement_id}/locations", response_model=MovementOut)
def update_movement_locations(
    movement_id: int,
    body: MovementLocationsUpdateIn,
    db: Session = Depends(get_db),
):
    movement = db.query(Movement).filter(Movement.id == movement_id).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")

    if movement.review_status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Only pending movements can be edited",
        )

    if body.from_location_id is not None:
        from_loc = db.query(Location).filter(Location.id == body.from_location_id).first()
        if not from_loc:
            raise HTTPException(status_code=404, detail="from_location not found")
        if not from_loc.is_active:
            raise HTTPException(status_code=409, detail="from_location is inactive")
        movement.from_location_id = body.from_location_id

    if body.to_location_id is not None:
        to_loc = db.query(Location).filter(Location.id == body.to_location_id).first()
        if not to_loc:
            raise HTTPException(status_code=404, detail="to_location not found")
        if not to_loc.is_active:
            raise HTTPException(status_code=409, detail="to_location is inactive")
        movement.to_location_id = body.to_location_id

    db.add(movement)

    movement_event = (
        db.query(RfidEventLog)
        .filter(
            RfidEventLog.movement_id == movement_id,
            RfidEventLog.event_type == "movement_created",
        )
        .order_by(RfidEventLog.created_at.desc())
        .first()
    )

    if movement_event:
        payload = dict(movement_event.payload_json or {})

        if body.from_location_id is not None:
            payload["from_location_id"] = body.from_location_id

        if body.to_location_id is not None:
            payload["to_location_id"] = body.to_location_id

        sync_payload = dict(payload.get("mysim_sync_payload") or {})
        row = dict(sync_payload.get("row") or {})

        if body.from_location_id is not None:
            sync_payload["source_location"] = body.from_location_id
            row["sourceLocation"] = body.from_location_id

        if body.to_location_id is not None:
            sync_payload["destination_location"] = body.to_location_id
            row["destinationLocation"] = body.to_location_id

        if row:
            sync_payload["row"] = row
            payload["mysim_sync_payload"] = sync_payload

        movement_event.payload_json = payload
        db.add(movement_event)

    db.commit()
    db.refresh(movement)

    return movement

@router.patch("/{movement_id}/quantity", response_model=MovementOut)
def update_movement_quantity(
    movement_id: int,
    body: MovementQuantityUpdateIn,
    db: Session = Depends(get_db),
):
    movement = db.query(Movement).filter(Movement.id == movement_id).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")

    if movement.review_status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Only pending movements can be edited",
        )

    if body.quantity <= 0:
        raise HTTPException(status_code=409, detail="Quantity must be greater than zero")

    movement.quantity = body.quantity
    db.add(movement)

    movement_event = (
        db.query(RfidEventLog)
        .filter(
            RfidEventLog.movement_id == movement_id,
            RfidEventLog.event_type == "movement_created",
        )
        .order_by(RfidEventLog.created_at.desc())
        .first()
    )

    if movement_event:
        payload = dict(movement_event.payload_json or {})
        payload["quantity"] = float(body.quantity)

        sync_payload = dict(payload.get("mysim_sync_payload") or {})
        row = dict(sync_payload.get("row") or {})
        row["quantity"] = float(body.quantity)

        if row:
            sync_payload["row"] = row
            payload["mysim_sync_payload"] = sync_payload

        movement_event.payload_json = payload
        db.add(movement_event)

    db.commit()
    db.refresh(movement)

    return movement