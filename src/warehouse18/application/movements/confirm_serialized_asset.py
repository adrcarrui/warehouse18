from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from warehouse18.domain.models import (
    Asset,
    AssetEnrichment,
    AssetLocation,
    IntegrationOutbox,
    Item,
    Location,
    Movement,
    MovementAsset,
    MovementType,
)


ALLOWED_GR_EXISTING_ASSET_STATUSES = {"active", "inactive", "repair"}
BLOCKED_GR_EXISTING_ASSET_STATUSES = {"lost", "scrapped"}

ALLOWED_GT_ASSET_STATUSES = {"active"}
ALLOWED_GI_ASSET_STATUSES = {"active"}


class ConfirmSerializedAssetError(ValueError):
    pass


@dataclass(frozen=True)
class ConfirmSerializedAssetResult:
    movement_id: int
    item_id: int
    asset_id: int
    movement_type_code: str
    asset_code: str
    item_code: str


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
        raise ConfirmSerializedAssetError("Movement type not found")

    code = (movement_type.code or "").strip().upper()

    if code not in {"GR", "GT", "GI"}:
        raise ConfirmSerializedAssetError(
            f"Unsupported movement type for serialized asset: {code}"
        )

    return code

def _try_return_existing_confirmation(
    db: Session,
    *,
    movement: Movement,
    movement_type_code: str,
    resolved_asset_code: str,
    resolved_item_code: str,
    create_enrichment: bool,
    enqueue_sync: bool,
) -> ConfirmSerializedAssetResult | None:
    """
    Idempotencia:
    Si el movimiento ya está vinculado a un asset, no volvemos a confirmar
    como si fuese nuevo.

    - Si coincide con el mismo asset_code: devolvemos OK.
    - Si intenta apuntar a otro asset: bloqueamos.
    """

    if movement.reference_type != "asset" or movement.reference_id is None:
        return None

    asset = (
        db.query(Asset)
        .filter(Asset.id == movement.reference_id)
        .first()
    )

    if asset is None:
        raise ConfirmSerializedAssetError(
            f"Movement {movement.id} is linked to missing asset {movement.reference_id}"
        )

    if not _same_code(asset.asset_code, resolved_asset_code):
        raise ConfirmSerializedAssetError(
            f"Movement {movement.id} is already linked to asset {asset.id} "
            f"with asset_code {asset.asset_code}, not {resolved_asset_code}"
        )

    item = None
    if asset.item_id is not None:
        item = (
            db.query(Item)
            .filter(Item.id == asset.item_id)
            .first()
        )

    if item is None:
        raise ConfirmSerializedAssetError(
            f"Asset {asset.id} linked to movement {movement.id} has no valid item"
        )

    if not _same_code(item.item_code, resolved_item_code):
        raise ConfirmSerializedAssetError(
            f"Movement {movement.id} is already linked to item {item.item_code}, "
            f"not {resolved_item_code}"
        )

    movement.item_id = item.id
    movement.quantity = Decimal("1")

    _link_movement_asset(
        db,
        movement=movement,
        asset=asset,
    )

    if create_enrichment:
        _ensure_asset_enrichment(db, asset=asset)

    if enqueue_sync:
        _enqueue_mysim_outbox_event(
            db,
            movement=movement,
            item=item,
            asset=asset,
            movement_type_code=movement_type_code,
        )

    db.flush()

    return ConfirmSerializedAssetResult(
        movement_id=movement.id,
        item_id=item.id,
        asset_id=asset.id,
        movement_type_code=movement_type_code,
        asset_code=asset.asset_code,
        item_code=item.item_code,
    )

def _get_or_create_serialized_item(
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
            raise ConfirmSerializedAssetError(
                f"Item {item_code} does not exist. Only GR can create new serialized items."
            )

        item = Item(
            item_code=item_code,
            name=f"Pending mySim sync - {item_code}",
            description="Created automatically from RFID serialized asset confirmation",
            category=None,
            uom="unit",
            is_serialized=True,
            is_active=True,
        )
        db.add(item)
        db.flush()
        return item

    if not item.is_serialized:
        raise ConfirmSerializedAssetError(
            f"Item {item_code} exists but is not serialized"
        )

    if not item.is_active:
        raise ConfirmSerializedAssetError(
            f"Item {item_code} is inactive"
        )

    return item


def _get_or_create_asset(
    db: Session,
    *,
    asset_code: str,
    item: Item,
    movement_type_code: str,
) -> Asset:
    asset = (
        db.query(Asset)
        .filter(Asset.asset_code == asset_code)
        .first()
    )

    if asset is None:
        if movement_type_code != "GR":
            raise ConfirmSerializedAssetError(
                f"Asset {asset_code} does not exist. Only GR can create new serialized assets."
            )

        asset = Asset(
            asset_code=asset_code,
            item_id=item.id,
            status="active",
        )
        db.add(asset)
        db.flush()
        return asset

    if asset.item_id is not None and asset.item_id != item.id:
        raise ConfirmSerializedAssetError(
            f"Asset {asset_code} is already linked to another item"
        )

    if asset.item_id is None:
        asset.item_id = item.id

    status = (asset.status or "").strip().lower()

    if movement_type_code == "GR":
        if status in BLOCKED_GR_EXISTING_ASSET_STATUSES:
            raise ConfirmSerializedAssetError(
                f"Asset {asset_code} has blocked status for GR: {asset.status}"
            )

        if status not in ALLOWED_GR_EXISTING_ASSET_STATUSES:
            raise ConfirmSerializedAssetError(
                f"Asset {asset_code} has unsupported status for GR: {asset.status}"
            )

        asset.status = "active"
        db.flush()
        return asset

    if movement_type_code == "GT":
        if status not in ALLOWED_GT_ASSET_STATUSES:
            raise ConfirmSerializedAssetError(
                f"Asset {asset_code} must be active for GT"
            )

        return asset

    if movement_type_code == "GI":
        if status not in ALLOWED_GI_ASSET_STATUSES:
            raise ConfirmSerializedAssetError(
                f"Asset {asset_code} must be active for GI"
            )

        return asset

    raise ConfirmSerializedAssetError(
        f"Unsupported movement type: {movement_type_code}"
    )

def _ensure_movement_can_be_linked_to_asset(
    *,
    movement: Movement,
    asset: Asset,
) -> None:
    if movement.reference_type is None and movement.reference_id is None:
        return

    if movement.reference_type == "asset" and movement.reference_id == asset.id:
        return

    if movement.reference_type == "asset" and movement.reference_id != asset.id:
        raise ConfirmSerializedAssetError(
            f"Movement {movement.id} is already linked to another asset: "
            f"{movement.reference_id}"
        )

    raise ConfirmSerializedAssetError(
        f"Movement {movement.id} is already linked to "
        f"{movement.reference_type}:{movement.reference_id}"
    )

def _update_asset_location(
    db: Session,
    *,
    asset: Asset,
    movement: Movement,
    movement_type_code: str,
) -> None:
    current_location = (
        db.query(AssetLocation)
        .filter(AssetLocation.asset_id == asset.id)
        .first()
    )

    if movement_type_code in {"GR", "GT"}:
        if movement.to_location_id is None:
            raise ConfirmSerializedAssetError(
                f"Movement {movement.id} requires to_location_id for {movement_type_code}"
            )

        if current_location is None:
            current_location = AssetLocation(
                asset_id=asset.id,
                location_id=movement.to_location_id,
            )
            db.add(current_location)
        else:
            current_location.location_id = movement.to_location_id

        asset.status = "active"
        db.flush()
        return

    if movement_type_code == "GI":
        if current_location is not None:
            db.delete(current_location)

        # De momento usamos inactive como "fuera del almacén".
        # Más adelante podemos añadir status='out', que sería más limpio.
        asset.status = "inactive"
        db.flush()
        return

    raise ConfirmSerializedAssetError(
        f"Unsupported movement type: {movement_type_code}"
    )


def _link_movement_asset(
    db: Session,
    *,
    movement: Movement,
    asset: Asset,
) -> None:
    existing = (
        db.query(MovementAsset)
        .filter(
            MovementAsset.movement_id == movement.id,
            MovementAsset.asset_id == asset.id,
        )
        .first()
    )

    if existing is None:
        db.add(
            MovementAsset(
                movement_id=movement.id,
                asset_id=asset.id,
                quantity=Decimal("1"),
            )
        )
    else:
        existing.quantity = Decimal("1")

    db.flush()


def _ensure_asset_enrichment(
    db: Session,
    *,
    asset: Asset,
) -> None:
    existing = (
        db.query(AssetEnrichment)
        .filter(AssetEnrichment.asset_id == asset.id)
        .first()
    )

    if existing is not None:
        return

    db.add(
        AssetEnrichment(
            asset_id=asset.id,
            sync_status="pending",
            retries=0,
        )
    )
    db.flush()


def _enqueue_mysim_outbox_event(
    db: Session,
    *,
    movement: Movement,
    item: Item,
    asset: Asset,
    movement_type_code: str,
    device_install_uninstall: dict | None = None,
) -> None:
    existing = (
        db.query(IntegrationOutbox)
        .filter(IntegrationOutbox.target_system == "mysim")
        .filter(IntegrationOutbox.entity_type == "movement")
        .filter(IntegrationOutbox.entity_id == movement.id)
        .filter(IntegrationOutbox.action == "sync")
        .filter(
            IntegrationOutbox.status.in_(
                ["pending", "processing", "sent", "error"]
            )
        )
        .filter(
            IntegrationOutbox.payload_json["movement_id"].astext == str(movement.id)
        )
        .first()
    )

    if existing is not None:
        return

    payload_json = {
        "movement_id": movement.id,
        "movement_type": movement_type_code,
        "item_id": item.id,
        "item_code": item.item_code,
        "asset_id": asset.id,
        "asset_code": asset.asset_code,
        "from_location_id": movement.from_location_id,
        "to_location_id": movement.to_location_id,
    }

    if device_install_uninstall:
        payload_json["device_install_uninstall"] = {
            "unistall_part": device_install_uninstall.get("unistall_part"),
            "dest_uninstalled_part": device_install_uninstall.get("dest_uninstalled_part"),
            "uninstalled_by": device_install_uninstall.get("uninstalled_by"),
            "why_is_it_uninstalled": device_install_uninstall.get("why_is_it_uninstalled"),
        }

    db.add(
        IntegrationOutbox(
            direction="outbound",
            target_system="mysim",
            entity_type="movement",
            entity_id=movement.id,
            action="serialized_asset_confirmed",
            payload_json={
                "movement_id": movement.id,
                "movement_type": movement_type_code,
                "item_id": item.id,
                "item_code": item.item_code,
                "asset_id": asset.id,
                "asset_code": asset.asset_code,
                "from_location_id": movement.from_location_id,
                "to_location_id": movement.to_location_id,
            },
            status="pending",
            retries=0,
        )
    )
    db.flush()

def _is_device_destination(db: Session, movement: Movement) -> bool:
    if movement.to_location_id is None:
        return False

    location = (
        db.query(Location)
        .filter(Location.id == movement.to_location_id)
        .first()
    )

    if location is None:
        return False

    code = str(getattr(location, "code", "") or "").strip().lower()
    name = str(getattr(location, "name", "") or "").strip().lower()

    return code == "1" or code == "device" or name == "device"

def confirm_serialized_asset_movement(
    db: Session,
    *,
    movement_id: int,
    asset_code: str | None = None,
    item_code: str | None = None,
    create_enrichment: bool = True,
    enqueue_sync: bool = True,

    # Device install/uninstall
    unistall_part: str | None = None,
    dest_uninstalled_part: int | None = None,
    uninstalled_by: int | None = None,
    why_is_it_uninstalled: str | None = None,
) -> ConfirmSerializedAssetResult:
    movement = (
        db.query(Movement)
        .filter(Movement.id == movement_id)
        .first()
    )

    if movement is None:
        raise ConfirmSerializedAssetError("Movement not found")

    movement_type_code = _get_movement_type_code(db, movement)

    is_device_destination = _is_device_destination(db, movement)

    if is_device_destination:
        missing = []

        if not unistall_part:
            missing.append("unistall_part")

        if dest_uninstalled_part is None:
            missing.append("dest_uninstalled_part")

        if uninstalled_by is None:
            missing.append("uninstalled_by")

        if not why_is_it_uninstalled:
            missing.append("why_is_it_uninstalled")

        if missing:
            raise ConfirmSerializedAssetError(
                "Device destination requires: " + ", ".join(missing)
            )

    resolved_asset_code = (
        _normalize_code(asset_code)
        or _normalize_code(getattr(movement, "detected_asset_code", None))
        or extract_epc_from_notes(movement.notes)
    )
    if resolved_asset_code is None:
        raise ConfirmSerializedAssetError(
            "asset_code is required or movement.notes must contain epc=..."
        )

    resolved_item_code = _normalize_code(item_code) or _normalize_code(movement.item_key)
    if resolved_item_code is None:
        raise ConfirmSerializedAssetError(
            "item_code is required or movement.item_key must be set"
        )

    existing_confirmation = _try_return_existing_confirmation(
        db,
        movement=movement,
        movement_type_code=movement_type_code,
        resolved_asset_code=resolved_asset_code,
        resolved_item_code=resolved_item_code,
        create_enrichment=create_enrichment,
        enqueue_sync=enqueue_sync,
    )

    if existing_confirmation is not None:
        return existing_confirmation

    item = _get_or_create_serialized_item(
        db,
        item_code=resolved_item_code,
        movement_type_code=movement_type_code,
    )

    asset = _get_or_create_asset(
        db,
        asset_code=resolved_asset_code,
        item=item,
        movement_type_code=movement_type_code,
    )

    _ensure_movement_can_be_linked_to_asset(
        movement=movement,
        asset=asset,
    )

    movement.item_id = item.id
    movement.quantity = Decimal("1")
    movement.reference_type = "asset"
    movement.reference_id = asset.id
    
    _update_asset_location(
        db,
        asset=asset,
        movement=movement,
        movement_type_code=movement_type_code,
    )

    _link_movement_asset(
        db,
        movement=movement,
        asset=asset,
    )

    if create_enrichment:
        _ensure_asset_enrichment(db, asset=asset)

    if enqueue_sync:
        device_payload = None

        if _is_device_destination(db, movement):
            device_payload = {
                "unistall_part": unistall_part,
                "dest_uninstalled_part": dest_uninstalled_part,
                "uninstalled_by": uninstalled_by,
                "why_is_it_uninstalled": why_is_it_uninstalled,
            }

        _enqueue_mysim_outbox_event(
            db,
            movement=movement,
            item=item,
            asset=asset,
            movement_type_code=movement_type_code,
            device_install_uninstall=device_payload,
        )

    db.flush()

    return ConfirmSerializedAssetResult(
        movement_id=movement.id,
        item_id=item.id,
        asset_id=asset.id,
        movement_type_code=movement_type_code,
        asset_code=asset.asset_code,
        item_code=item.item_code,
    )