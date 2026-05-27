from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from warehouse18.domain.models import (
    IntegrationOutbox,
    InventoryStock,
    Item,
    Location,
    Movement,
    MovementType,
    StockContainer,
    movement,
)


class ConfirmBulkMovementError(ValueError):
    pass


@dataclass(frozen=True)
class ConfirmBulkMovementResult:
    movement_id: int
    item_id: int
    item_code: str
    container_id: int
    container_code: str
    movement_type_code: str
    quantity: Decimal


def extract_epc_from_notes(notes: str | None) -> str | None:
    if not notes:
        return None

    match = re.search(r"(?:^|[\s|,;])epc\s*=\s*([^|\s,;]+)", notes, re.IGNORECASE)
    if not match:
        return None

    return match.group(1).strip()


def _normalize_code(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _same_code(left: str | None, right: str | None) -> bool:
    normalized_left = _normalize_code(left)
    normalized_right = _normalize_code(right)

    if normalized_left is None or normalized_right is None:
        return False

    return normalized_left.upper() == normalized_right.upper()


def _get_movement_type_code(db: Session, movement: Movement) -> str:
    movement_type = (
        db.query(MovementType)
        .filter(MovementType.id == movement.movement_type_id)
        .first()
    )

    if movement_type is None:
        raise ConfirmBulkMovementError("Movement type not found")

    code = (movement_type.code or "").strip().upper()

    if code not in {"GR", "GT", "GI"}:
        raise ConfirmBulkMovementError(
            f"Unsupported movement type for bulk movement: {code}"
        )

    return code


def _get_quantity(movement: Movement) -> Decimal:
    if movement.quantity is None:
        raise ConfirmBulkMovementError("Movement quantity is required for bulk movement")

    qty = Decimal(str(movement.quantity))

    if qty <= 0:
        raise ConfirmBulkMovementError("Movement quantity must be greater than zero")

    return qty


def _get_or_create_bulk_item(
    db: Session,
    *,
    item_code: str,
    movement_type_code: str,
) -> Item:
    item = (
        db.query(Item)
        .filter(Item.item_code == item_code)
        .first()
    )

    if item is None:
        if movement_type_code != "GR":
            raise ConfirmBulkMovementError(
                f"Item {item_code} does not exist. Only GR can create new bulk items."
            )

        item = Item(
            item_code=item_code,
            name=f"Pending mySim sync - {item_code}",
            description="Created automatically from RFID bulk confirmation",
            category=None,
            uom="unit",
            is_serialized=False,
            is_active=True,
        )
        db.add(item)
        db.flush()
        return item

    if item.is_serialized:
        raise ConfirmBulkMovementError(
            f"Item {item_code} exists but is serialized"
        )

    if not item.is_active:
        raise ConfirmBulkMovementError(
            f"Item {item_code} is inactive"
        )

    return item


def _get_location_or_error(
    db: Session,
    *,
    location_id: int | None,
    field_name: str,
) -> Location:
    if location_id is None:
        raise ConfirmBulkMovementError(f"{field_name} is required")

    location = (
        db.query(Location)
        .filter(Location.id == location_id)
        .first()
    )

    if location is None:
        raise ConfirmBulkMovementError(f"{field_name} not found")

    if not location.is_active:
        raise ConfirmBulkMovementError(f"{field_name} is inactive")

    return location

def _touch_stock_row(
    stock: InventoryStock,
    *,
    movement: Movement,
) -> None:
    stock.last_movement_id = movement.id
    stock.updated_at = datetime.now(timezone.utc)

def _get_or_create_stock_row(
    db: Session,
    *,
    item_id: int,
    location_id: int,
) -> InventoryStock:
    stock = (
        db.query(InventoryStock)
        .filter(InventoryStock.item_id == item_id)
        .filter(InventoryStock.location_id == location_id)
        .with_for_update()
        .first()
    )

    if stock is not None:
        return stock

    stock = InventoryStock(
        item_id=item_id,
        location_id=location_id,
        quantity=Decimal("0"),
    )
    db.add(stock)
    db.flush()
    return stock


def _get_container(
    db: Session,
    *,
    container_code: str,
) -> StockContainer | None:
    return (
        db.query(StockContainer)
        .filter(StockContainer.container_code == container_code)
        .with_for_update()
        .first()
    )


def _ensure_movement_can_be_linked_to_container(
    *,
    movement: Movement,
    container: StockContainer,
) -> None:
    if movement.reference_type is None and movement.reference_id is None:
        return

    if movement.reference_type == "container" and movement.reference_id == container.id:
        return

    if movement.reference_type == "container" and movement.reference_id != container.id:
        raise ConfirmBulkMovementError(
            f"Movement {movement.id} is already linked to another container: "
            f"{movement.reference_id}"
        )

    raise ConfirmBulkMovementError(
        f"Movement {movement.id} is already linked to "
        f"{movement.reference_type}:{movement.reference_id}"
    )

def _confirm_gr(
    db: Session,
    *,
    movement: Movement,
    item: Item,
    container_code: str,
    quantity: Decimal,
) -> StockContainer:
    to_location = _get_location_or_error(
        db,
        location_id=movement.to_location_id,
        field_name="to_location_id",
    )

    if not to_location.is_warehouse_location:
        raise ConfirmBulkMovementError(
            "Good Receipt destination must be inside the warehouse"
        )

    container = _get_container(db, container_code=container_code)

    if container is None:
        container = StockContainer(
            container_code=container_code,
            item_id=item.id,
            location_id=to_location.id,
            quantity=quantity,
            status="open",
            is_active=True,
        )
        db.add(container)
        db.flush()
    else:
        if container.item_id != item.id:
            raise ConfirmBulkMovementError(
                f"Container {container_code} is already linked to another item"
            )

        container.location_id = to_location.id
        container.quantity = Decimal(str(container.quantity)) + quantity
        container.status = "open"
        container.is_active = True
        db.flush()

    stock = _get_or_create_stock_row(
        db,
        item_id=item.id,
        location_id=to_location.id,
    )

    stock.quantity = Decimal(str(stock.quantity)) + quantity
    _touch_stock_row(stock, movement=movement)

    movement.from_location_id = None
    movement.to_location_id = to_location.id

    db.flush()
    return container

def _confirm_gi(
    db: Session,
    *,
    movement: Movement,
    item: Item,
    container_code: str,
    quantity: Decimal,
) -> StockContainer:
    to_location = _get_location_or_error(
        db,
        location_id=movement.to_location_id,
        field_name="to_location_id",
    )

    if to_location.is_warehouse_location:
        raise ConfirmBulkMovementError(
            "Good Issue destination must be outside the warehouse"
        )

    container = _get_container(db, container_code=container_code)

    if container is None:
        raise ConfirmBulkMovementError(
            f"Container {container_code} does not exist. GI cannot create containers."
        )

    if container.item_id != item.id:
        raise ConfirmBulkMovementError(
            f"Container {container_code} is linked to another item"
        )

    if not container.is_active:
        raise ConfirmBulkMovementError(
            f"Container {container_code} is inactive"
        )

    current_qty = Decimal(str(container.quantity))

    if current_qty < quantity:
        raise ConfirmBulkMovementError(
            f"Not enough quantity in container {container_code}. "
            f"Available={current_qty}, requested={quantity}"
        )

    origin_location_id = container.location_id

    stock = _get_or_create_stock_row(
        db,
        item_id=item.id,
        location_id=origin_location_id,
    )

    stock_qty = Decimal(str(stock.quantity))

    if stock_qty < quantity:
        raise ConfirmBulkMovementError(
            f"Not enough inventory stock for item {item.item_code}. "
            f"Available={stock_qty}, requested={quantity}"
        )

    container.quantity = current_qty - quantity

    if container.quantity == Decimal("0"):
        container.status = "empty"

    stock.quantity = Decimal(str(stock.quantity)) - quantity
    _touch_stock_row(stock, movement=movement)

    movement.from_location_id = origin_location_id
    movement.to_location_id = to_location.id

    db.flush()
    return container

def _confirm_gt(
    db: Session,
    *,
    movement: Movement,
    item: Item,
    container_code: str,
    quantity: Decimal,
) -> StockContainer:
    to_location = _get_location_or_error(
        db,
        location_id=movement.to_location_id,
        field_name="to_location_id",
    )

    if not to_location.is_warehouse_location:
        raise ConfirmBulkMovementError(
            "Good Transfer destination must be inside the warehouse"
        )

    container = _get_container(db, container_code=container_code)

    if container is None:
        raise ConfirmBulkMovementError(
            f"Container {container_code} does not exist. GT cannot create containers."
        )

    if container.item_id != item.id:
        raise ConfirmBulkMovementError(
            f"Container {container_code} is linked to another item"
        )

    if not container.is_active:
        raise ConfirmBulkMovementError(
            f"Container {container_code} is inactive"
        )

    current_qty = Decimal(str(container.quantity or 0))

    if quantity <= 0:
        raise ConfirmBulkMovementError(
            f"Movement quantity must be greater than zero. Movement quantity={quantity}"
        )

    if current_qty <= 0:
        raise ConfirmBulkMovementError(
            f"Container {container_code} has no available quantity. "
            f"Container quantity={current_qty}"
        )

    if quantity > current_qty:
        raise ConfirmBulkMovementError(
            f"Movement quantity cannot be greater than container quantity. "
            f"Container quantity={current_qty}, movement quantity={quantity}"
        )

    origin_location_id = movement.from_location_id or container.location_id

    if origin_location_id is None:
        raise ConfirmBulkMovementError(
            "GT requires an origin location"
        )

    if origin_location_id == to_location.id:
        raise ConfirmBulkMovementError(
            f"Origin and destination are the same location"
        )

    origin_stock = _get_or_create_stock_row(
        db,
        item_id=item.id,
        location_id=origin_location_id,
    )

    destination_stock = _get_or_create_stock_row(
        db,
        item_id=item.id,
        location_id=to_location.id,
    )

    origin_stock_qty = Decimal(str(origin_stock.quantity or 0))
    destination_stock_qty = Decimal(str(destination_stock.quantity or 0))

    if origin_stock_qty < quantity:
        raise ConfirmBulkMovementError(
            f"Not enough inventory stock at origin. "
            f"Available={origin_stock_qty}, requested={quantity}"
        )

    # Stock real:
    # GT -> resta en origen y suma en destino
    origin_stock.quantity = origin_stock_qty - quantity
    _touch_stock_row(origin_stock, movement=movement)

    destination_stock.quantity = destination_stock_qty + quantity
    _touch_stock_row(destination_stock, movement=movement)

    # Contenedor:
    # - Si se mueve todo el contenedor, el contenedor cambia de ubicación.
    # - Si se mueve solo una parte, el contenedor original se queda en origen
    #   con la cantidad restante.
    if quantity == current_qty:
        container.location_id = to_location.id
        container.quantity = current_qty
        container.status = "open"
    else:
        container.quantity = current_qty - quantity
        container.status = "open"

    movement.from_location_id = origin_location_id
    movement.to_location_id = to_location.id

    db.flush()
    return container

def _try_return_existing_confirmation(
    db: Session,
    *,
    movement: Movement,
    movement_type_code: str,
    resolved_container_code: str,
    resolved_item_code: str,
) -> ConfirmBulkMovementResult | None:
    if movement.reference_type != "container" or movement.reference_id is None:
        return None

    container = (
        db.query(StockContainer)
        .filter(StockContainer.id == movement.reference_id)
        .first()
    )

    if container is None:
        raise ConfirmBulkMovementError(
            f"Movement {movement.id} is linked to missing container {movement.reference_id}"
        )

    if not _same_code(container.container_code, resolved_container_code):
        raise ConfirmBulkMovementError(
            f"Movement {movement.id} is already linked to container "
            f"{container.container_code}, not {resolved_container_code}"
        )

    item = (
        db.query(Item)
        .filter(Item.id == container.item_id)
        .first()
    )

    if item is None:
        raise ConfirmBulkMovementError(
            f"Container {container.id} has no valid item"
        )

    if not _same_code(item.item_code, resolved_item_code):
        raise ConfirmBulkMovementError(
            f"Movement {movement.id} is already linked to item {item.item_code}, "
            f"not {resolved_item_code}"
        )

    qty = _get_quantity(movement)

    return ConfirmBulkMovementResult(
        movement_id=movement.id,
        item_id=item.id,
        item_code=item.item_code,
        container_id=container.id,
        container_code=container.container_code,
        movement_type_code=movement_type_code,
        quantity=qty,
    )


def _enqueue_bulk_outbox_event(
    db: Session,
    *,
    movement: Movement,
    item: Item,
    container: StockContainer,
    movement_type_code: str,
    quantity: Decimal,
) -> None:
    existing = (
        db.query(IntegrationOutbox)
        .filter(IntegrationOutbox.target_system == "mysim")
        .filter(IntegrationOutbox.entity_type == "container")
        .filter(IntegrationOutbox.entity_id == container.id)
        .filter(IntegrationOutbox.action == "bulk_movement_confirmed")
        .filter(IntegrationOutbox.status.in_(["pending", "processing", "sent", "error"]))
        .filter(IntegrationOutbox.payload_json["movement_id"].astext == str(movement.id))
        .first()
    )

    if existing is not None:
        return

    db.add(
        IntegrationOutbox(
            direction="outbound",
            target_system="mysim",
            entity_type="container",
            entity_id=container.id,
            action="bulk_movement_confirmed",
            payload_json={
                "movement_id": movement.id,
                "movement_type": movement_type_code,
                "item_id": item.id,
                "item_code": item.item_code,
                "container_id": container.id,
                "container_code": container.container_code,
                "quantity": str(quantity),
                "from_location_id": movement.from_location_id,
                "to_location_id": movement.to_location_id,
            },
            status="pending",
            retries=0,
        )
    )

    db.flush()

def confirm_bulk_movement(
    db: Session,
    *,
    movement_id: int,
    container_code: str | None = None,
    item_code: str | None = None,
    enqueue_sync: bool = True,
) -> ConfirmBulkMovementResult:
    movement = (
        db.query(Movement)
        .filter(Movement.id == movement_id)
        .first()
    )

    if movement is None:
        raise ConfirmBulkMovementError("Movement not found")

    movement_type_code = _get_movement_type_code(db, movement)

    resolved_container_code = (
        _normalize_code(container_code)
        or _normalize_code(getattr(movement, "detected_asset_code", None))
        or extract_epc_from_notes(movement.notes)
    )

    if resolved_container_code is None:
        raise ConfirmBulkMovementError(
            "container_code is required or movement.detected_asset_code must be set"
        )

    resolved_item_code = _normalize_code(item_code) or _normalize_code(movement.item_key)

    if resolved_item_code is None:
        raise ConfirmBulkMovementError(
            "item_code is required or movement.item_key must be set"
        )

    existing_confirmation = _try_return_existing_confirmation(
        db,
        movement=movement,
        movement_type_code=movement_type_code,
        resolved_container_code=resolved_container_code,
        resolved_item_code=resolved_item_code,
    )

    if existing_confirmation is not None:
        return existing_confirmation

    quantity = _get_quantity(movement)

    item = _get_or_create_bulk_item(
        db,
        item_code=resolved_item_code,
        movement_type_code=movement_type_code,
    )

    if movement_type_code == "GR":
        container = _confirm_gr(
            db,
            movement=movement,
            item=item,
            container_code=resolved_container_code,
            quantity=quantity,
        )
    elif movement_type_code == "GI":
        container = _confirm_gi(
            db,
            movement=movement,
            item=item,
            container_code=resolved_container_code,
            quantity=quantity,
        )
    elif movement_type_code == "GT":
        container = _confirm_gt(
            db,
            movement=movement,
            item=item,
            container_code=resolved_container_code,
            quantity=quantity,
        )
    else:
        raise ConfirmBulkMovementError(
            f"Unsupported movement type: {movement_type_code}"
        )

    _ensure_movement_can_be_linked_to_container(
        movement=movement,
        container=container,
    )

    movement.item_id = item.id
    movement.quantity = quantity
    movement.reference_type = "container"
    movement.reference_id = container.id

    if enqueue_sync:
        _enqueue_bulk_outbox_event(
            db,
            movement=movement,
            item=item,
            container=container,
            movement_type_code=movement_type_code,
            quantity=quantity,
        )

    db.flush()

    return ConfirmBulkMovementResult(
        movement_id=movement.id,
        item_id=item.id,
        item_code=item.item_code,
        container_id=container.id,
        container_code=container.container_code,
        movement_type_code=movement_type_code,
        quantity=quantity,
    )