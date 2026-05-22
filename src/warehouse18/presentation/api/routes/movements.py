from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, select, text, Integer, cast
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
    AisleDeviceGroup
)
from warehouse18.presentation.api.schemas import (
    MovementCreateIn,
    MovementOut,
    MovementQuantityUpdateIn,
    MovementConfirmIn,
    MovementRejectIn,
    MovementLocationsUpdateIn,
    PageOut,
    CandidateLocationsOut,
    MovementSetDestinationIn,
    MovementTypeUpdateIn,
    MovementDescriptionUpdateIn,
    ConfirmSerializedAssetIn,
    ConfirmSerializedAssetOut,
    ConfirmBulkMovementIn,
    ConfirmBulkMovementOut,
)
from warehouse18.application.movements.confirm_serialized_asset import (
    ConfirmSerializedAssetError,
    confirm_serialized_asset_movement,
)
from warehouse18.application.movements.confirm_bulk_movement import (
    ConfirmBulkMovementError,
    confirm_bulk_movement,
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

def is_device_group_allowed_in_aisle(
    db: Session,
    *,
    aisle_id: int,
    device_group_id: int,
) -> bool:
    return (
        db.query(AisleDeviceGroup)
        .filter(AisleDeviceGroup.aisle_id == aisle_id)
        .filter(AisleDeviceGroup.device_group_id == device_group_id)
        .filter(AisleDeviceGroup.is_active.is_(True))
        .first()
        is not None
    )


def get_allowed_device_group_codes_for_aisle(
    db: Session,
    *,
    aisle_id: int,
) -> list[str]:
    rows = (
        db.query(DeviceGroup.code)
        .join(
            AisleDeviceGroup,
            AisleDeviceGroup.device_group_id == DeviceGroup.id,
        )
        .filter(AisleDeviceGroup.aisle_id == aisle_id)
        .filter(AisleDeviceGroup.is_active.is_(True))
        .filter(DeviceGroup.is_active.is_(True))
        .order_by(AisleDeviceGroup.is_primary.desc(), DeviceGroup.code.asc())
        .all()
    )

    return [str(row[0]) for row in rows]

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

    if movement_code in {"GR", "GT", "GI"}:
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

        if not is_device_group_allowed_in_aisle(
            db,
            aisle_id=aisle.id,
            device_group_id=device_group.id,
        ):
            allowed_codes = get_allowed_device_group_codes_for_aisle(
                db,
                aisle_id=aisle.id,
            )

            raise HTTPException(
                status_code=409,
                detail=(
                    f"Wrong aisle: item group '{device_group.code}' is not allowed "
                    f"in aisle '{aisle.code}'. Allowed groups: "
                    f"{', '.join(allowed_codes) if allowed_codes else 'none'}"
                ),
            )

        if location.aisle_id != aisle.id:
            raise HTTPException(
                status_code=409,
                detail="Location does not belong to the detected aisle",
            )

        if location.device_group_id != device_group.id:
            raise HTTPException(
                status_code=409,
                detail="Location does not belong to the detected aisle",
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


def normalize_item_prefix(item_key: str | None) -> str:
    if not item_key:
        return ""

    return item_key.split("-", 1)[0].strip().upper()


def resolve_location_context(item_key: str | None) -> tuple[str, list[str], str]:
    """
    Devuelve:
    - item_prefix: prefijo real del item, por ejemplo 295
    - allowed_device_group_codes: grupos válidos para comprobar aisle_device_groups
    - location_prefix: prefijo real de las localizaciones en tabla locations

    Ejemplos:
    295-0197   -> item_prefix=295,  groups=[295, C295],   location_prefix=C295
    C295-0197  -> item_prefix=C295, groups=[295, C295],   location_prefix=C295
    235-15922  -> item_prefix=235,  groups=[235, CN235],  location_prefix=CN235
    CN235-15922-> item_prefix=CN235,groups=[235, CN235],  location_prefix=CN235
    """
    item_prefix = normalize_item_prefix(item_key)

    if item_prefix in {"295", "C295"}:
        return item_prefix, ["295", "C295"], "C295"

    if item_prefix in {"235", "CN235"}:
        return item_prefix, ["235", "CN235"], "CN235"

    return item_prefix, [item_prefix], item_prefix


def aisle_allows_device_group(
    db: Session,
    *,
    aisle_id: int,
    device_group_codes: list[str],
) -> DeviceGroup | None:
    return (
        db.query(DeviceGroup)
        .join(
            AisleDeviceGroup,
            AisleDeviceGroup.device_group_id == DeviceGroup.id,
        )
        .filter(AisleDeviceGroup.aisle_id == aisle_id)
        .filter(AisleDeviceGroup.is_active.is_(True))
        .filter(DeviceGroup.code.in_(device_group_codes))
        .order_by(DeviceGroup.code.asc())
        .first()
    )


@router.get(
    "/{movement_id}/candidate-locations",
    response_model=CandidateLocationsOut,
)
def get_candidate_locations(
    movement_id: int,
    db: Session = Depends(get_db),
) -> CandidateLocationsOut:
    mv = (
        db.query(Movement)
        .filter(Movement.id == movement_id)
        .first()
    )

    if mv is None:
        raise HTTPException(
            status_code=404,
            detail=f"Movement {movement_id} not found",
        )

    movement_type = (
        db.query(MovementType)
        .filter(MovementType.id == mv.movement_type_id)
        .first()
    )

    if movement_type is None:
        raise HTTPException(
            status_code=409,
            detail="Movement type not found",
        )

    movement_code = (movement_type.code or "").strip().upper()

    if movement_code not in {"GR","GT", "GI"}:
        raise HTTPException(
            status_code=409,
            detail=f"Unsupported movement type: {movement_code}",
        )

    if not mv.item_key:
        raise HTTPException(
            status_code=409,
            detail="Movement has no item_key",
        )
    # GOOD ISSUE:
    # Para GI mostramos todas las localizaciones activas.
    # No depende de detected_aisle_id ni de device_group.
    if movement_code == "GI":
        locations = (
            db.query(Location)
            .filter(Location.is_active.is_(True))
            .order_by(
                Location.name.asc(),
                Location.code.asc(),
            )
            .all()
        )

        return CandidateLocationsOut(
            item_key=mv.item_key,
            item_prefix=normalize_item_prefix(mv.item_key),
            aisle_code=None,
            device_group_code=None,
            locations=locations,
        )

    if mv.detected_aisle_id is None:
        raise HTTPException(
            status_code=409,
            detail="Movement has no detected aisle",
        )

    aisle = (
        db.query(Aisle)
        .filter(Aisle.id == mv.detected_aisle_id)
        .first()
    )

    if aisle is None:
        raise HTTPException(
            status_code=409,
            detail="Detected aisle not found",
        )

    item_prefix, device_group_codes, location_prefix = resolve_location_context(
        mv.item_key
    )

    device_group = aisle_allows_device_group(
        db,
        aisle_id=aisle.id,
        device_group_codes=device_group_codes,
    )

    if device_group is None:
        return CandidateLocationsOut(
            item_key=mv.item_key,
            item_prefix=item_prefix,
            aisle_code=aisle.code,
            device_group_code=location_prefix,
            locations=[],
        )

    locations = (
        db.query(Location)
        .filter(Location.aisle_id == aisle.id)
        .filter(Location.is_active.is_(True))
        .filter(Location.code.ilike(f"{location_prefix} %"))
        .order_by(
            cast(Location.rack_code, Integer).asc(),
            Location.shelf_code.asc(),
            Location.name.asc(),
        )
        .all()
    )

    return CandidateLocationsOut(
        item_key=mv.item_key,
        item_prefix=item_prefix,
        aisle_code=aisle.code,
        device_group_code=location_prefix,
        locations=locations,
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

@router.patch("/{movement_id}/quantity", response_model=MovementOut)
def update_movement_quantity(
    movement_id: int,
    body: MovementQuantityUpdateIn,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()

    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    qty = body.quantity

    if qty != qty.to_integral_value():
        raise HTTPException(
            status_code=409,
            detail="Quantity must be an integer",
        )

    if qty <= 0:
        raise HTTPException(
            status_code=409,
            detail="Quantity must be greater than zero",
        )

    mv.quantity = qty

    try:
        db.commit()
        db.refresh(mv)
        return mv
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))
    
@router.post(
    "/{movement_id}/confirm-serialized-asset",
    response_model=ConfirmSerializedAssetOut,
)
def confirm_serialized_asset_endpoint(
    movement_id: int,
    payload: ConfirmSerializedAssetIn,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()
    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    if mv.review_status == REVIEW_STATUS_REJECTED:
        raise HTTPException(status_code=409, detail="Movement already rejected")

    if payload.reviewed_by_user_id is not None:
        reviewer = db.query(User).filter(User.id == payload.reviewed_by_user_id).first()
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

    try:
        result = confirm_serialized_asset_movement(
            db,
            movement_id=movement_id,
            asset_code=payload.asset_code,
            item_code=payload.item_code,
            create_enrichment=payload.create_enrichment,
            enqueue_sync=payload.enqueue_sync,
        )

        reason = _compute_report_reason_for_confirmation(mv, movement_type_name)

        mv.review_status = REVIEW_STATUS_CONFIRMED
        mv.reviewed_at = datetime.now(timezone.utc)
        mv.reviewed_by_user_id = payload.reviewed_by_user_id
        mv.review_note = payload.review_note

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

        close_pending_and_set_cooldown_for_review(
            movement_id=mv.id,
            source="confirm_serialized_asset",
        )

        return ConfirmSerializedAssetOut(
            status="ok",
            movement_id=result.movement_id,
            movement_type_code=result.movement_type_code,
            item_id=result.item_id,
            item_code=result.item_code,
            asset_id=result.asset_id,
            asset_code=result.asset_code,
            message="Serialized asset movement confirmed",
        )

    except ConfirmSerializedAssetError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Serialized asset confirmation failed: {exc}",
        ) from exc

    except ConfirmSerializedAssetError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Serialized asset confirmation failed: {exc}",
        ) from exc
    
@router.post(
    "/{movement_id}/confirm-bulk",
    response_model=ConfirmBulkMovementOut,
)
def confirm_bulk_movement_endpoint(
    movement_id: int,
    payload: ConfirmBulkMovementIn,
    db: Session = Depends(get_db),
):
    mv = db.query(Movement).filter(Movement.id == movement_id).first()
    if not mv:
        raise HTTPException(status_code=409, detail="Movement not found")

    if mv.review_status == REVIEW_STATUS_REJECTED:
        raise HTTPException(status_code=409, detail="Movement already rejected")

    if payload.reviewed_by_user_id is not None:
        reviewer = db.query(User).filter(User.id == payload.reviewed_by_user_id).first()
        if not reviewer:
            raise HTTPException(status_code=409, detail="Reviewer user not found")

    try:
        result = confirm_bulk_movement(
            db,
            movement_id=movement_id,
            container_code=payload.container_code,
            item_code=payload.item_code,
            enqueue_sync=payload.enqueue_sync,
        )

        movement_type_name = _movement_type_name(db, mv.movement_type_id)
        reason = _compute_report_reason_for_confirmation(mv, movement_type_name)

        mv.review_status = REVIEW_STATUS_CONFIRMED
        mv.reviewed_at = datetime.now(timezone.utc)
        mv.reviewed_by_user_id = payload.reviewed_by_user_id
        mv.review_note = payload.review_note

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

        close_pending_and_set_cooldown_for_review(
            movement_id=mv.id,
            source="confirm_bulk",
        )

        return ConfirmBulkMovementOut(
            status="ok",
            movement_id=result.movement_id,
            movement_type_code=result.movement_type_code,
            item_id=result.item_id,
            item_code=result.item_code,
            container_id=result.container_id,
            container_code=result.container_code,
            quantity=result.quantity,
            message="Bulk movement confirmed",
        )

    except ConfirmBulkMovementError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Bulk confirmation failed: {exc}",
        ) from exc