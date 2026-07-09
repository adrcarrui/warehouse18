from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse18.application.rfid.epc96 import load_epc_schema, parse_epc96
from warehouse18.domain.models import (
    Asset,
    AssetLocation,
    InventoryStock,
    Item,
    Location,
    StockContainer,
)
from warehouse18.infrastructure.db import get_db


router = APIRouter(tags=["handheld_inventory"])


REPO_ROOT = Path(__file__).resolve().parents[5]
EPC_SCHEMA_PATH = REPO_ROOT / "config" / "epc_schema.json"


class HandheldValidateScanIn(BaseModel):
    epc: str = Field(min_length=1)
    reader_id: str | None = "zebra-mc3300r-01"
    operator_id: int | None = None


def _location_or_409(db: Session, location_id: int) -> Location:
    loc = (
        db.query(Location)
        .filter(Location.id == location_id)
        .filter(Location.is_active.is_(True))
        .first()
    )

    if not loc:
        raise HTTPException(status_code=409, detail="Location not found or inactive")

    return loc


def _load_epc_display_padding() -> dict[str, int]:
    try:
        raw = json.loads(EPC_SCHEMA_PATH.read_text(encoding="utf-8"))
        display_padding = raw.get("display_padding", {}) or {}
        return {str(k).upper(): int(v) for k, v in display_padding.items()}
    except Exception:
        return {}


def _resolve_epc_candidates(epc: str) -> dict[str, Any]:
    epc = epc.strip().upper()

    schema = load_epc_schema(EPC_SCHEMA_PATH)
    parsed = parse_epc96(epc, schema)

    if parsed.magic != schema.magic:
        raise ValueError("Invalid EPC magic")

    if parsed.version != schema.version:
        raise ValueError("Invalid EPC version")

    if not parsed.checksum_ok:
        raise ValueError("Invalid EPC checksum")

    if not parsed.family_name:
        raise ValueError("Unknown EPC family")

    family = parsed.family_name.strip().upper()
    serial = int(parsed.serial)

    padding_by_family = _load_epc_display_padding()
    family_padding = padding_by_family.get(family, 6)

    candidates: list[str] = []

    def add(value: str) -> None:
        value = value.strip().upper()
        if value and value not in candidates:
            candidates.append(value)

    add(f"{family}-{serial:0{family_padding}d}")
    add(f"{family}-{serial:06d}")
    add(f"{family}-{serial}")

    return {
        "epc": epc,
        "family": family,
        "serial": serial,
        "candidates": candidates,
    }


def _item_dict(item: Item | None) -> dict[str, Any] | None:
    if not item:
        return None

    return {
        "id": int(item.id),
        "item_code": item.item_code,
        "name": item.name,
        "description": item.description,
        "category": item.category,
        "uom": item.uom,
        "is_serialized": bool(item.is_serialized),
        "is_active": bool(item.is_active),
    }


def _location_dict(location: Location | None) -> dict[str, Any] | None:
    if not location:
        return None

    return {
        "id": int(location.id),
        "code": location.code,
        "name": location.name,
        "type": location.type,
        "parent_id": location.parent_id,
    }

@router.get("/handheld-inventory-submits/{audit_id}")
def get_handheld_inventory_submit_detail(
    audit_id: int,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("""
            SELECT
                id AS audit_id,
                at,
                entity_id AS location_id,
                after_json
            FROM audit_log
            WHERE id = :audit_id
              AND action = 'HANDHELD_INVENTORY_SUBMIT'
            LIMIT 1
        """),
        {"audit_id": audit_id},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Handheld inventory submit not found",
        )

    payload = row["after_json"]

    if isinstance(payload, str):
        payload = json.loads(payload)

    if payload is None:
        payload = {}

    return {
        "audit_id": row["audit_id"],
        "at": row["at"],
        "location_id": row["location_id"],
        "location_label": payload.get("location_label"),
        "reader_id": payload.get("reader_id"),
        "total_items": payload.get("total_items", 0),
        "ok_items": payload.get("ok_items", 0),
        "pending_items": payload.get("pending_items", 0),
        "rows": payload.get("rows", []),
        "payload": payload,
    }

@router.get("/handheld-inventory-submits")
def list_handheld_inventory_submits(
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT
                id,
                at,
                entity_id AS location_id,
                after_json->>'location_label' AS location_label,
                after_json->>'reader_id' AS reader_id,
                (after_json->>'total_items')::int AS total_items,
                (after_json->>'ok_items')::int AS ok_items,
                (after_json->>'pending_items')::int AS pending_items
            FROM audit_log
            WHERE action = 'HANDHELD_INVENTORY_SUBMIT'
            ORDER BY at DESC
            LIMIT 50
        """)
    ).mappings().all()

    return {
        "items": [dict(row) for row in rows]
    }

@router.get("/locations/{location_id}/handheld-inventory")
def get_handheld_inventory_for_location(
    location_id: int,
    db: Session = Depends(get_db),
):
    loc = _location_or_409(db, location_id)

    asset_rows = (
        db.query(Asset, Item)
        .join(AssetLocation, AssetLocation.asset_id == Asset.id)
        .outerjoin(Item, Item.id == Asset.item_id)
        .filter(AssetLocation.location_id == location_id)
        .filter(Asset.status != "inactive")
        .order_by(Asset.asset_code.asc())
        .all()
    )

    container_rows = (
        db.query(StockContainer, Item)
        .outerjoin(Item, Item.id == StockContainer.item_id)
        .filter(StockContainer.location_id == location_id)
        .filter(StockContainer.is_active.is_(True))
        .order_by(StockContainer.container_code.asc())
        .all()
    )

    stock_rows = (
        db.query(InventoryStock, Item)
        .outerjoin(Item, Item.id == InventoryStock.item_id)
        .filter(InventoryStock.location_id == location_id)
        .filter(InventoryStock.quantity > 0)
        .order_by(InventoryStock.item_id.asc())
        .all()
    )

    assets = [
        {
            "type": "asset",
            "asset_id": int(asset.id),
            "asset_code": asset.asset_code,
            "status": asset.status,
            "item": _item_dict(item),
        }
        for asset, item in asset_rows
    ]

    containers = [
        {
            "type": "container",
            "container_id": int(container.id),
            "container_code": container.container_code,
            "quantity": container.quantity,
            "status": container.status,
            "item": _item_dict(item),
        }
        for container, item in container_rows
    ]

    stock_items = [
        {
            "type": "stock",
            "stock_id": int(stock.id),
            "quantity": stock.quantity,
            "item": _item_dict(item),
        }
        for stock, item in stock_rows
    ]

    return {
        "location": _location_dict(loc),
        "summary": {
            "assets_expected": len(assets),
            "containers_expected": len(containers),
            "stock_lines": len(stock_items),
        },
        "assets": assets,
        "containers": containers,
        "stock_items": stock_items,
    }


@router.post("/locations/{location_id}/handheld-inventory/validate-scan")
def validate_handheld_scan_for_location(
    location_id: int,
    body: HandheldValidateScanIn,
    db: Session = Depends(get_db),
):
    selected_location = _location_or_409(db, location_id)
    raw_epc = body.epc.strip().upper()

    # ---------------------------------------------------------------------
    # 1) PRIMERO: buscar EPC exacto como contenedor RFID.
    # Esto es lo importante para Zebra/DataWedge.
    # No intentamos parsear el EPC antes de mirar si ya está mapeado.
    # ---------------------------------------------------------------------
    container_row = (
        db.query(StockContainer, Item, Location)
        .outerjoin(Item, Item.id == StockContainer.item_id)
        .outerjoin(Location, Location.id == StockContainer.location_id)
        .filter(StockContainer.container_code == raw_epc)
        .first()
    )

    if container_row:
        container, item, current_location = container_row

        if not container.is_active:
            return {
                "status": "ok",
                "validation": "inactive_container",
                "severity": "error",
                "message": "Container exists but is inactive",
                "epc": raw_epc,
                "object_type": "container",
                "container_id": int(container.id),
                "container_code": container.container_code,
                "quantity": float(container.quantity) if container.quantity is not None else None,
                "container_status": container.status,
                "item": _item_dict(item),
                "selected_location": _location_dict(selected_location),
                "current_location": _location_dict(current_location),
            }

        if int(container.location_id) == int(location_id):
            return {
                "status": "ok",
                "validation": "expected",
                "severity": "success",
                "message": "Container belongs to this location",
                "epc": raw_epc,
                "object_type": "container",
                "container_id": int(container.id),
                "container_code": container.container_code,
                "quantity": float(container.quantity) if container.quantity is not None else None,
                "container_status": container.status,
                "item": _item_dict(item),
                "selected_location": _location_dict(selected_location),
                "current_location": _location_dict(current_location),
            }

        return {
            "status": "ok",
            "validation": "wrong_location",
            "severity": "warning",
            "message": "Container exists but belongs to another location",
            "epc": raw_epc,
            "object_type": "container",
            "container_id": int(container.id),
            "container_code": container.container_code,
            "quantity": float(container.quantity) if container.quantity is not None else None,
            "container_status": container.status,
            "item": _item_dict(item),
            "selected_location": _location_dict(selected_location),
            "current_location": _location_dict(current_location),
        }

    # ---------------------------------------------------------------------
    # 2) SEGUNDO: buscar EPC exacto como asset_code.
    # Por si algún asset físico tiene el EPC real guardado como asset_code.
    # ---------------------------------------------------------------------
    asset_row_exact = (
        db.query(Asset, Item, AssetLocation, Location)
        .outerjoin(Item, Item.id == Asset.item_id)
        .outerjoin(AssetLocation, AssetLocation.asset_id == Asset.id)
        .outerjoin(Location, Location.id == AssetLocation.location_id)
        .filter(Asset.asset_code == raw_epc)
        .first()
    )

    if asset_row_exact:
        asset, item, asset_location, current_location = asset_row_exact

        if asset.status == "inactive":
            return {
                "status": "ok",
                "validation": "inactive_asset",
                "severity": "error",
                "message": "Asset exists but is inactive",
                "epc": raw_epc,
                "object_type": "asset",
                "asset_id": int(asset.id),
                "asset_code": asset.asset_code,
                "asset_status": asset.status,
                "item": _item_dict(item),
                "selected_location": _location_dict(selected_location),
                "current_location": _location_dict(current_location),
            }

        if asset_location and int(asset_location.location_id) == int(location_id):
            return {
                "status": "ok",
                "validation": "expected",
                "severity": "success",
                "message": "Asset belongs to this location",
                "epc": raw_epc,
                "object_type": "asset",
                "asset_id": int(asset.id),
                "asset_code": asset.asset_code,
                "asset_status": asset.status,
                "item": _item_dict(item),
                "selected_location": _location_dict(selected_location),
                "current_location": _location_dict(current_location),
            }

        return {
            "status": "ok",
            "validation": "wrong_location",
            "severity": "warning",
            "message": "Asset exists but belongs to another location",
            "epc": raw_epc,
            "object_type": "asset",
            "asset_id": int(asset.id),
            "asset_code": asset.asset_code,
            "asset_status": asset.status,
            "item": _item_dict(item),
            "selected_location": _location_dict(selected_location),
            "current_location": _location_dict(current_location),
        }

    # ---------------------------------------------------------------------
    # 3) TERCERO: solo si no está mapeado exacto, intentar parsear como EPC
    # interno de Warehouse18.
    # ---------------------------------------------------------------------
    try:
        resolved = _resolve_epc_candidates(raw_epc)
    except Exception as e:
        return {
            "status": "ignored",
            "validation": "invalid_or_unmapped_epc",
            "severity": "error",
            "message": f"EPC is not mapped as a container/asset and could not be parsed: {e}",
            "epc": raw_epc,
            "location": _location_dict(selected_location),
        }

    epc = resolved["epc"]
    family = resolved["family"]
    serial = resolved["serial"]
    candidates = resolved["candidates"]

    if family == "USER":
        return {
            "status": "ignored",
            "validation": "user_epc",
            "severity": "warning",
            "message": "User EPC ignored in shelf inventory validation",
            "epc": epc,
            "family": family,
            "serial": serial,
            "candidates": candidates,
            "location": _location_dict(selected_location),
        }

    # ---------------------------------------------------------------------
    # 4) Buscar asset por candidatos generados desde EPC interno.
    # Ejemplo: EPC interno -> CN235-015771
    # ---------------------------------------------------------------------
    asset_row = (
        db.query(Asset, Item, AssetLocation, Location)
        .outerjoin(Item, Item.id == Asset.item_id)
        .outerjoin(AssetLocation, AssetLocation.asset_id == Asset.id)
        .outerjoin(Location, Location.id == AssetLocation.location_id)
        .filter(Asset.asset_code.in_(candidates))
        .first()
    )

    if asset_row:
        asset, item, asset_location, current_location = asset_row

        if asset.status == "inactive":
            return {
                "status": "ok",
                "validation": "inactive_asset",
                "severity": "error",
                "message": "Asset exists but is inactive",
                "epc": epc,
                "resolved_key": asset.asset_code,
                "object_type": "asset",
                "asset_id": int(asset.id),
                "asset_code": asset.asset_code,
                "asset_status": asset.status,
                "item": _item_dict(item),
                "selected_location": _location_dict(selected_location),
                "current_location": _location_dict(current_location),
            }

        if asset_location and int(asset_location.location_id) == int(location_id):
            return {
                "status": "ok",
                "validation": "expected",
                "severity": "success",
                "message": "Asset belongs to this location",
                "epc": epc,
                "resolved_key": asset.asset_code,
                "object_type": "asset",
                "asset_id": int(asset.id),
                "asset_code": asset.asset_code,
                "asset_status": asset.status,
                "item": _item_dict(item),
                "selected_location": _location_dict(selected_location),
                "current_location": _location_dict(current_location),
            }

        return {
            "status": "ok",
            "validation": "wrong_location",
            "severity": "warning",
            "message": "Asset exists but belongs to another location",
            "epc": epc,
            "resolved_key": asset.asset_code,
            "object_type": "asset",
            "asset_id": int(asset.id),
            "asset_code": asset.asset_code,
            "asset_status": asset.status,
            "item": _item_dict(item),
            "selected_location": _location_dict(selected_location),
            "current_location": _location_dict(current_location),
        }

    # ---------------------------------------------------------------------
    # 5) Buscar contenedor por candidatos generados.
    # ---------------------------------------------------------------------
    container_row = (
        db.query(StockContainer, Item, Location)
        .outerjoin(Item, Item.id == StockContainer.item_id)
        .outerjoin(Location, Location.id == StockContainer.location_id)
        .filter(StockContainer.container_code.in_(candidates))
        .first()
    )

    if container_row:
        container, item, current_location = container_row

        if not container.is_active:
            return {
                "status": "ok",
                "validation": "inactive_container",
                "severity": "error",
                "message": "Container exists but is inactive",
                "epc": epc,
                "resolved_key": container.container_code,
                "object_type": "container",
                "container_id": int(container.id),
                "container_code": container.container_code,
                "quantity": float(container.quantity) if container.quantity is not None else None,
                "container_status": container.status,
                "item": _item_dict(item),
                "selected_location": _location_dict(selected_location),
                "current_location": _location_dict(current_location),
            }

        if int(container.location_id) == int(location_id):
            return {
                "status": "ok",
                "validation": "expected",
                "severity": "success",
                "message": "Container belongs to this location",
                "epc": epc,
                "resolved_key": container.container_code,
                "object_type": "container",
                "container_id": int(container.id),
                "container_code": container.container_code,
                "quantity": float(container.quantity) if container.quantity is not None else None,
                "container_status": container.status,
                "item": _item_dict(item),
                "selected_location": _location_dict(selected_location),
                "current_location": _location_dict(current_location),
            }

        return {
            "status": "ok",
            "validation": "wrong_location",
            "severity": "warning",
            "message": "Container exists but belongs to another location",
            "epc": epc,
            "resolved_key": container.container_code,
            "object_type": "container",
            "container_id": int(container.id),
            "container_code": container.container_code,
            "quantity": float(container.quantity) if container.quantity is not None else None,
            "container_status": container.status,
            "item": _item_dict(item),
            "selected_location": _location_dict(selected_location),
            "current_location": _location_dict(current_location),
        }

    # ---------------------------------------------------------------------
    # 6) Buscar item por candidatos generados.
    # Esto vale para stock no serializado cuando el EPC interno genera item_code.
    # ---------------------------------------------------------------------
    item = (
        db.query(Item)
        .filter(Item.item_code.in_(candidates))
        .filter(Item.is_active.is_(True))
        .first()
    )

    if item:
        stock_here = (
            db.query(InventoryStock)
            .filter(InventoryStock.location_id == location_id)
            .filter(InventoryStock.item_id == item.id)
            .filter(InventoryStock.quantity > 0)
            .first()
        )

        if stock_here:
            return {
                "status": "ok",
                "validation": "expected_stock_item",
                "severity": "success",
                "message": "Item has stock in this location",
                "epc": epc,
                "resolved_key": item.item_code,
                "object_type": "item",
                "item": _item_dict(item),
                "quantity": float(stock_here.quantity) if stock_here.quantity is not None else None,
                "selected_location": _location_dict(selected_location),
                "current_location": _location_dict(selected_location),
            }

        other_stock = (
            db.query(InventoryStock, Location)
            .join(Location, Location.id == InventoryStock.location_id)
            .filter(InventoryStock.item_id == item.id)
            .filter(InventoryStock.quantity > 0)
            .first()
        )

        return {
            "status": "ok",
            "validation": "item_exists_no_stock_here",
            "severity": "warning",
            "message": "Item exists but no stock was found in this location",
            "epc": epc,
            "resolved_key": item.item_code,
            "object_type": "item",
            "item": _item_dict(item),
            "selected_location": _location_dict(selected_location),
            "current_location": _location_dict(other_stock[1]) if other_stock else None,
        }

    # ---------------------------------------------------------------------
    # 7) No encontrado.
    # ---------------------------------------------------------------------
    return {
        "status": "ok",
        "validation": "unknown_epc",
        "severity": "error",
        "message": "EPC was not found as asset, container or item",
        "epc": epc,
        "family": family,
        "serial": serial,
        "candidates": candidates,
        "selected_location": _location_dict(selected_location),
    }

@router.get("/handheld/resolve-item")
def resolve_handheld_item(
    q: str,
    db: Session = Depends(get_db),
):
    """
    Resolve a barcode/item/container/asset code and return its current registered location.

    Used by handheld Search tag:
    GET /api/handheld/resolve-item?q=CN235-015922
    """

    search = q.strip()

    if not search:
        raise HTTPException(status_code=400, detail="Missing q")

    row = db.execute(
        text(
            """
            WITH candidates AS (
                ----------------------------------------------------------------
                -- 1) Exact asset match
                ----------------------------------------------------------------
                SELECT
                    10 AS priority,
                    'asset' AS object_type,
                    a.id AS object_id,
                    a.asset_code AS display_code,
                    i.item_code AS item_code,
                    a.asset_code AS epc,
                    l.id AS location_id,
                    l.code AS location_code,
                    l.name AS location_name,
                    al.since AS last_movement_at
                FROM assets a
                JOIN items i
                    ON i.id = a.item_id
                LEFT JOIN asset_location al
                    ON al.asset_id = a.id
                LEFT JOIN locations l
                    ON l.id = al.location_id
                WHERE
                    a.status != 'inactive'
                    AND UPPER(a.asset_code) = UPPER(:search)

                UNION ALL

                ----------------------------------------------------------------
                -- 2) Exact container match
                ----------------------------------------------------------------
                SELECT
                    20 AS priority,
                    'container' AS object_type,
                    sc.id AS object_id,
                    sc.container_code AS display_code,
                    i.item_code AS item_code,
                    sc.container_code AS epc,
                    l.id AS location_id,
                    l.code AS location_code,
                    l.name AS location_name,
                    NULL::timestamp AS last_movement_at
                FROM stock_containers sc
                JOIN items i
                    ON i.id = sc.item_id
                LEFT JOIN locations l
                    ON l.id = sc.location_id
                WHERE
                    sc.is_active = true
                    AND UPPER(sc.container_code) = UPPER(:search)

                UNION ALL

                ----------------------------------------------------------------
                -- 3) Item code found as serialized asset
                ----------------------------------------------------------------
                SELECT
                    30 AS priority,
                    'asset' AS object_type,
                    a.id AS object_id,
                    a.asset_code AS display_code,
                    i.item_code AS item_code,
                    a.asset_code AS epc,
                    l.id AS location_id,
                    l.code AS location_code,
                    l.name AS location_name,
                    al.since AS last_movement_at
                FROM assets a
                JOIN items i
                    ON i.id = a.item_id
                LEFT JOIN asset_location al
                    ON al.asset_id = a.id
                LEFT JOIN locations l
                    ON l.id = al.location_id
                WHERE
                    a.status != 'inactive'
                    AND i.is_active = true
                    AND UPPER(i.item_code) = UPPER(:search)

                UNION ALL

                ----------------------------------------------------------------
                -- 4) Item code found as tagged container
                ----------------------------------------------------------------
                SELECT
                    40 AS priority,
                    'container' AS object_type,
                    sc.id AS object_id,
                    sc.container_code AS display_code,
                    i.item_code AS item_code,
                    sc.container_code AS epc,
                    l.id AS location_id,
                    l.code AS location_code,
                    l.name AS location_name,
                    NULL::timestamp AS last_movement_at
                FROM stock_containers sc
                JOIN items i
                    ON i.id = sc.item_id
                LEFT JOIN locations l
                    ON l.id = sc.location_id
                WHERE
                    sc.is_active = true
                    AND i.is_active = true
                    AND UPPER(i.item_code) = UPPER(:search)

                UNION ALL

                ----------------------------------------------------------------
                -- 5) Item code found as stock line
                ----------------------------------------------------------------
                SELECT
                    50 AS priority,
                    'stock' AS object_type,
                    s.id AS object_id,
                    i.item_code AS display_code,
                    i.item_code AS item_code,
                    NULL::text AS epc,
                    l.id AS location_id,
                    l.code AS location_code,
                    l.name AS location_name,
                    NULL::timestamp AS last_movement_at
                FROM inventory_stock s
                JOIN items i
                    ON i.id = s.item_id
                LEFT JOIN locations l
                    ON l.id = s.location_id
                WHERE
                    s.quantity > 0
                    AND i.is_active = true
                    AND UPPER(i.item_code) = UPPER(:search)
            )
            SELECT *
            FROM candidates
            ORDER BY
                priority ASC,
                location_name NULLS LAST,
                display_code NULLS LAST
            LIMIT 1
            """
        ),
        {"search": search},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Item, asset or container not found: {search}",
        )

    last_movement_at = row["last_movement_at"]

    if hasattr(last_movement_at, "isoformat"):
        last_movement_at = last_movement_at.isoformat()

    location = None

    if row["location_id"] is not None:
        location = {
            "id": int(row["location_id"]),
            "code": row["location_code"],
            "name": row["location_name"],
        }

    return {
        "found": True,
        "object_type": row["object_type"],
        "object_id": int(row["object_id"]),
        "display_code": row["display_code"],
        "item_code": row["item_code"],
        "epc": row["epc"] or "",
        "location": location,
        "last_movement_at": last_movement_at,
    }