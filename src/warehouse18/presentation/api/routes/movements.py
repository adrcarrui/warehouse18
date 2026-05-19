from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, select, text
from datetime import datetime, timezone

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import (
    Movement,
    MovementType,
    Item,
    Location,
    User,
    Aisle,
    DeviceAlias,
    DeviceGroup,
)
from warehouse18.presentation.api.schemas import (
    MovementCreateIn,
    MovementOut,
    MovementConfirmIn,
    MovementRejectIn,
    MovementLocationsUpdateIn,
    PageOut,
    CandidateLocationsOut,
    MovementSetDestinationIn,
    MovementTypeUpdateIn,
    MovementDescriptionUpdateIn,
)
from warehouse18.presentation.api.paging import paginate
from warehouse18.presentation.api.pagination_headers import set_pagination_headers
from warehouse18.application.rfid.door_engine import close_pending_and_set_cooldown_for_review

router = APIRouter(prefix="/movements", tags=["movements"])

VALID_REF_TYPES = {"asset", "container"}

REVIEW_STATUS_PENDING = "pending"
REVIEW_STATUS_CONFIRMED = "confirmed"
REVIEW_STATUS_REJECTED = "rejected"

MYSIM_SYNC_STATUS_PENDING_REVIEW = "pending_review"
MYSIM_SYNC_STATUS_QUEUED = "queued"
MYSIM_SYNC_STATUS_NOT_SENT = "not_sent"

VALID_MOVEMENT_CODES = {"GI", "GR", "GT"}

MOVEMENT_TYPE_ALIASES = {
    "GI": "GI",
    "ISSUE": "GI",
    "GOOD ISSUE": "GI",
    "GOODS ISSUE": "GI",
    "GR": "GR",
    "RECEIPT": "GR",
    "GOOD RECEIPT": "GR",
    "GOODS RECEIPT": "GR",
    "GT": "GT",
    "TRANSFER": "GT",
    "GOOD TRANSFER": "GT",
    "GOODS TRANSFER": "GT",
}


def extract_item_prefix(item_key: str) -> str:
    value = (item_key or "").strip().upper()

    if not value:
        raise HTTPException(status_code=409, detail="movement.item_key is required")

    if "-" not in value:
        raise HTTPException(
            status_code=409,
            detail="movement.item_key must contain a prefix separated by '-'",
        )

    prefix = value.split("-", 1)[0].strip()

    if not prefix:
        raise HTTPException(status_code=409, detail="movement.item_key prefix is empty")

    return prefix


def resolve_device_group_from_item_key(
    db: Session,
    item_key: str,
) -> tuple[str, DeviceGroup]:
    prefix = extract_item_prefix(item_key)

    row = (
        db.query(DeviceAlias, DeviceGroup)
        .join(DeviceGroup, DeviceGroup.id == DeviceAlias.device_group_id)
        .filter(DeviceAlias.alias_code == prefix)
        .filter(DeviceAlias.is_active.is_(True))
        .filter(DeviceGroup.is_active.is_(True))
        .first()
    )

    if not row:
        raise HTTPException(
            status_code=409,
            detail=f"No active device group alias found for prefix '{prefix}'",
        )

    _, device_group = row
    return prefix, device_group


def normalize_movement_type_code(value: str | None) -> str:
    code = (value or "").strip().upper()
    normalized = MOVEMENT_TYPE_ALIASES.get(code)

    if normalized not in VALID_MOVEMENT_CODES:
        raise HTTPException(
            status_code=409,
            detail="movement_type_code must be GI, GR or GT",
        )

    return normalized


def get_movement_type_or_409(db: Session, movement_type_id: int) -> MovementType:
    mt = db.query(MovementType).filter(MovementType.id == movement_type_id).first()

    if not mt:
        raise HTTPException(status_code=409, detail="movement_type not found")

    return mt


def movement_type_code_of(mt: MovementType) -> str:
    code = (mt.code or "").strip().upper()

    if code in VALID_MOVEMENT_CODES:
        return code

    normalized = MOVEMENT_TYPE_ALIASES.get(code)
    if normalized in VALID_MOVEMENT_CODES:
        return normalized

    name = (mt.name or "").strip().upper()
    normalized = MOVEMENT_TYPE_ALIASES.get(name)
    if normalized in VALID_MOVEMENT_CODES:
        return normalized

    raise HTTPException(
        status_code=409,
        detail=f"Unsupported movement type: {mt.code or mt.name}",
    )


def _movement_type_name(db: Session, movement_type_id: int) -> str | None:
    mt = db.query(MovementType).filter(MovementType.id == movement_type_id).first()
    if not mt:
        return None
    return mt.name


def _compute_report_reason_for_confirmation(
    mv: Movement,
    movement_type_name: str | None,
) -> str | None:
    missing_user = mv.user_id is None

    missing_destination = False
    if movement_type_name in {"Goods Receipt", "Goods Transfer", "Goods Issue"}:
        missing_destination = mv.to_location_id is None

    if missing_user and missing_destination:
        return "missing_user_and_destination"
    if missing_user:
        return "missing_user"
    if missing_destination:
        return "missing_destination"

    return None


def get_detected_aisle_or_409(db: Session, mv: Movement) -> Aisle:
    if mv.detected_aisle_id is None:
        raise HTTPException(
            status_code=409,
            detail="Movement has no detected_aisle_id",
        )

    aisle = (
        db.query(Aisle)
        .filter(Aisle.id == mv.detected_aisle_id)
        .filter(Aisle.is_active.is_(True))
        .first()
    )

    if not aisle:
        raise HTTPException(
            status_code=409,
            detail="Movement detected aisle not found or inactive",
        )

    return aisle


def validate_destination_for_movement(
    db: Session,
    *,
    movement: Movement,
    location: Location,
) -> None:
    mt = get_movement_type_or_409(db, movement.movement_type_id)
    movement_code = movement_type_code_of(mt)

    if movement_code == "GI":
        if location.is_warehouse_location:
            raise HTTPException(
                status_code=409,
                detail="Good Issue destination must be outside the warehouse",
            )
        return

    if movement_code in {"GR", "GT"}:
        if not movement.item_key:
            raise HTTPException(
                status_code=409,
                detail="Movement has no item_key",
            )

        aisle = get_detected_aisle_or_409(db, movement)
        _, device_group = resolve_device_group_from_item_key(db, movement.item_key)

        if not location.is_warehouse_location:
            raise HTTPException(
                status_code=409,
                detail="Good Receipt/Transfer destination must be inside the warehouse",
            )

        if location.aisle_id != aisle.id:
            raise HTTPException(
                status_code=409,
                detail="Location does not belong to the detected aisle",
            )

        if location.device_group_id != device_group.id:
            raise HTTPException(
                status_code=409,
                detail="Location does not belong to the movement device group",
            )

        return

    raise HTTPException(
        status_code=409,
        detail=f"Unsupported movement type: {movement_code}",
    )


@router.post("/", response_model=MovementOut)
def create_movement(body: MovementCreateIn, db: Session = Depends(get_db)):
    mt = db.query(MovementType).filter(MovementType.id == body.movement_type_id).first()
    if not mt:
        raise HTTPException(status_code=409, detail="movement_type not found")

    if mt.affects_stock:
        if body.item_id is None:
            raise HTTPException(
                status_code=409,
                detail="item_id is required for stock-affecting movement",
            )
        if body.quantity is None:
            raise HTTPException(
                status_code=409,
                detail="quantity is required for stock-affecting movement",
            )

        it = db.query(Item).filter(Item.id == body.item_id).first()
        if not it:
            raise HTTPException(status_code=409, detail="Item not found")

    if mt.affects_location:
        if body.from_location_id is None and body.to_location_id is None:
            raise HTTPException(
                status_code=409,
                detail="from_location_id or to_location_id is required for location-affecting movement",
            )

        if body.from_location_id is not None:
            if not db.query(Location).filter(Location.id == body.from_location_id).first():
                raise HTTPException(status_code=409, detail="from_location not found")

        if body.to_location_id is not None:
            if not db.query(Location).filter(Location.id == body.to_location_id).first():
                raise HTTPException(status_code=409, detail="to_location not found")

    if (body.reference_type is None) != (body.reference_id is None):
        raise HTTPException(
            status_code=409,
            detail="reference_type and reference_id must be provided together",
        )

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


@router.get("/{movement_id}/candidate-locations", response_model=CandidateLocationsOut)
def candidate_locations_for_movement(
    movement_id: int,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()

    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    if not mv.item_key:
        raise HTTPException(
            status_code=409,
            detail="Movement has no item_key",
        )

    mt = get_movement_type_or_409(db, mv.movement_type_id)
    movement_code = movement_type_code_of(mt)

    prefix, device_group = resolve_device_group_from_item_key(db, mv.item_key)

    if movement_code == "GI":
        aisle_code = ""

        if mv.detected_aisle_id is not None:
            aisle = db.query(Aisle).filter(Aisle.id == mv.detected_aisle_id).first()
            aisle_code = aisle.code if aisle else ""

        locations = (
            db.query(Location)
            .filter(Location.is_active.is_(True))
            .filter(Location.is_warehouse_location.is_(False))
            .order_by(Location.name.asc(), Location.code.asc())
            .all()
        )

        return CandidateLocationsOut(
            item_key=mv.item_key,
            item_prefix=prefix,
            aisle_code=aisle_code,
            device_group_code=device_group.code,
            locations=locations,
        )

    if movement_code in {"GR", "GT"}:
        aisle = get_detected_aisle_or_409(db, mv)

        locations = (
            db.query(Location)
            .filter(Location.is_active.is_(True))
            .filter(Location.is_warehouse_location.is_(True))
            .filter(Location.aisle_id == aisle.id)
            .filter(Location.device_group_id == device_group.id)
            .order_by(
                Location.rack_code.asc(),
                Location.shelf_code.asc(),
                Location.name.asc(),
            )
            .all()
        )

        return CandidateLocationsOut(
            item_key=mv.item_key,
            item_prefix=prefix,
            aisle_code=aisle.code,
            device_group_code=device_group.code,
            locations=locations,
        )

    raise HTTPException(
        status_code=409,
        detail=f"Unsupported movement type: {movement_code}",
    )


@router.patch("/{movement_id}/movement-type", response_model=MovementOut)
def set_movement_type(
    movement_id: int,
    body: MovementTypeUpdateIn,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()

    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    if mv.review_status != REVIEW_STATUS_PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Movement cannot be edited because review_status is '{mv.review_status}'",
        )

    normalized_code = normalize_movement_type_code(body.movement_type_code)

    mt = (
        db.query(MovementType)
        .filter(MovementType.code == normalized_code)
        .first()
    )

    if not mt:
        raise HTTPException(
            status_code=409,
            detail=f"Movement type not found: {normalized_code}",
        )

    if mv.movement_type_id == mt.id:
        return mv

    mv.movement_type_id = mt.id

    # El destino anterior puede dejar de ser válido al cambiar de GR/GT a GI, o al revés.
    mv.to_location_id = None

    db.add(mv)
    db.commit()
    db.refresh(mv)

    return mv


@router.patch("/{movement_id}/destination", response_model=MovementOut)
def set_movement_destination(
    movement_id: int,
    body: MovementSetDestinationIn,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()

    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    if mv.review_status != REVIEW_STATUS_PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Movement cannot be edited because review_status is '{mv.review_status}'",
        )

    location = (
        db.query(Location)
        .filter(Location.id == body.location_id)
        .filter(Location.is_active.is_(True))
        .first()
    )

    if not location:
        raise HTTPException(status_code=409, detail="Location not found or inactive")

    validate_destination_for_movement(
        db,
        movement=mv,
        location=location,
    )

    mv.to_location_id = location.id

    db.add(mv)
    db.commit()
    db.refresh(mv)

    return mv


@router.patch("/{movement_id}/description", response_model=MovementOut)
def update_movement_description(
    movement_id: int,
    body: MovementDescriptionUpdateIn,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()

    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    if mv.review_status != REVIEW_STATUS_PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Movement cannot be edited because review_status is '{mv.review_status}'",
        )

    mv.notes = body.notes

    db.add(mv)
    db.commit()
    db.refresh(mv)

    return mv

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

    mt = get_movement_type_or_409(db, mv.movement_type_id)
    movement_code = movement_type_code_of(mt)

    if movement_code in {"GI", "GR", "GT"} and mv.to_location_id is None:
        raise HTTPException(
            status_code=409,
            detail="Destination location is required before confirming this movement",
        )

    if mv.to_location_id is not None:
        location = db.query(Location).filter(Location.id == mv.to_location_id).first()
        if not location:
            raise HTTPException(status_code=409, detail="Destination location not found")

        validate_destination_for_movement(
            db,
            movement=mv,
            location=location,
        )

    reason = _compute_report_reason_for_confirmation(mv, movement_type_name)

    mv.review_status = REVIEW_STATUS_CONFIRMED
    mv.reviewed_at = datetime.now(timezone.utc)
    mv.reviewed_by_user_id = body.reviewed_by_user_id
    mv.review_note = body.review_note

    mv.needs_report = reason is not None
    mv.report_reason = reason

    mv.mysim_sync_status = MYSIM_SYNC_STATUS_QUEUED

    db.add(mv)
    db.flush()

    existing_outbox = db.execute(
        text(
            """
            SELECT id
            FROM integration_outbox
            WHERE direction = 'outbound'
              AND target_system = 'mysim'
              AND entity_type = 'movement'
              AND entity_id = :movement_id
              AND action = 'sync'
              AND status IN ('pending', 'processing', 'error')
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {"movement_id": mv.id},
    ).first()

    if existing_outbox is None:
        db.execute(
            text(
                """
                INSERT INTO integration_outbox (
                    direction,
                    target_system,
                    entity_type,
                    entity_id,
                    action,
                    payload_json,
                    status,
                    retries,
                    created_at
                )
                VALUES (
                    'outbound',
                    'mysim',
                    'movement',
                    :movement_id,
                    'sync',
                    CAST(:payload_json AS jsonb),
                    'pending',
                    0,
                    now()
                )
                """
            ),
            {
                "movement_id": mv.id,
                "payload_json": "{}",
            },
        )

    db.commit()
    db.refresh(mv)

    close_pending_and_set_cooldown_for_review(
        movement_id=mv.id,
        source="confirm",
    )

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

    close_pending_and_set_cooldown_for_review(
        movement_id=mv.id,
        source="reject",
    )

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

    if mv.review_status != REVIEW_STATUS_PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Movement cannot be edited because review_status is '{mv.review_status}'",
        )

    if body.from_location_id is not None:
        from_loc = db.query(Location).filter(Location.id == body.from_location_id).first()
        if not from_loc:
            raise HTTPException(status_code=409, detail="from_location not found")
        mv.from_location_id = body.from_location_id

    if body.to_location_id is not None:
        to_loc = (
            db.query(Location)
            .filter(Location.id == body.to_location_id)
            .filter(Location.is_active.is_(True))
            .first()
        )
        if not to_loc:
            raise HTTPException(status_code=409, detail="to_location not found or inactive")

        validate_destination_for_movement(
            db,
            movement=mv,
            location=to_loc,
        )

        mv.to_location_id = body.to_location_id

    db.add(mv)
    db.commit()
    db.refresh(mv)

    return mv