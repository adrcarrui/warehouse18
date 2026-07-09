from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.presentation.api.schemas import (
    InventoryPartOut,
    ShelfInventoryOut,
    WarehouseDeviceGroupPartOut,
    WarehouseDeviceGroupPartsOut,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/shelves/{location_id}/parts", response_model=ShelfInventoryOut)
def get_shelf_parts(
    location_id: int,
    db: Session = Depends(get_db),
) -> ShelfInventoryOut:
    location = db.execute(
        text(
            """
            SELECT
                id,
                code,
                name,
                rack_code,
                shelf_code,
                aisle_id,
                device_group_id
            FROM locations
            WHERE id = :location_id
              AND is_active = true
              AND is_warehouse_location = true
            """
        ),
        {"location_id": location_id},
    ).mappings().first()

    if location is None:
        raise HTTPException(
            status_code=404,
            detail=f"Shelf location not found or inactive: {location_id}",
        )

    rows = db.execute(
        text(
            """
            WITH target_location AS (
                SELECT
                    id,
                    code,
                    name,
                    rack_code,
                    shelf_code,
                    aisle_id,
                    device_group_id
                FROM locations
                WHERE id = :location_id
                  AND is_active = true
                  AND is_warehouse_location = true
            )
            SELECT
                'serialized' AS source_type,
                i.id AS item_id,
                i.item_code,
                a.id AS asset_id,
                a.asset_code,
                1::numeric AS quantity,
                l.id AS location_id,
                l.code AS location_code,
                l.name AS location_name,
                l.rack_code,
                l.shelf_code,
                l.aisle_id
            FROM assets a
            JOIN items i ON i.id = a.item_id
            JOIN target_location l ON l.id = a.current_location_id

            UNION ALL

            SELECT
                'stock' AS source_type,
                i.id AS item_id,
                i.item_code,
                NULL::bigint AS asset_id,
                NULL::text AS asset_code,
                s.quantity,
                l.id AS location_id,
                l.code AS location_code,
                l.name AS location_name,
                l.rack_code,
                l.shelf_code,
                l.aisle_id
            FROM inventory_stock s
            JOIN items i ON i.id = s.item_id
            JOIN target_location l ON l.id = s.location_id
            WHERE s.quantity > 0

            ORDER BY item_code, asset_code NULLS LAST
            """
        ),
        {"location_id": location_id},
    ).mappings().all()

    parts = [InventoryPartOut(**dict(row)) for row in rows]

    return ShelfInventoryOut(
        location_id=location["id"],
        location_code=location["code"],
        location_name=location["name"],
        rack_code=location["rack_code"],
        shelf_code=location["shelf_code"],
        aisle_id=location["aisle_id"],
        parts=parts,
    )

@router.get(
    "/device-groups/{device_group_code}/warehouse-parts",
    response_model=WarehouseDeviceGroupPartsOut,
)
def get_warehouse_parts_by_device_group(
    device_group_code: str,
    db: Session = Depends(get_db),
) -> WarehouseDeviceGroupPartsOut:
    device_group = db.execute(
        text(
            """
            SELECT
                id,
                code
            FROM device_groups
            WHERE UPPER(code) = UPPER(:device_group_code)
              AND is_active = true
            """
        ),
        {"device_group_code": device_group_code.strip()},
    ).mappings().first()

    if device_group is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device group not found or inactive: {device_group_code}",
        )

    prefix_rows = db.execute(
        text(
            """
            SELECT code AS prefix
            FROM device_groups
            WHERE id = :device_group_id

            UNION

            SELECT alias_code AS prefix
            FROM device_aliases
            WHERE device_group_id = :device_group_id
              AND is_active = true

            ORDER BY prefix
            """
        ),
        {"device_group_id": device_group["id"]},
    ).mappings().all()

    matched_prefixes = [str(row["prefix"]) for row in prefix_rows if row["prefix"]]

    if not matched_prefixes:
        raise HTTPException(
            status_code=404,
            detail=f"No prefixes found for device group: {device_group_code}",
        )

    rows = db.execute(
        text(
            """
            WITH matched_prefixes AS (
                SELECT code AS prefix
                FROM device_groups
                WHERE id = :device_group_id

                UNION

                SELECT alias_code AS prefix
                FROM device_aliases
                WHERE device_group_id = :device_group_id
                  AND is_active = true
            ),
            warehouse_locations AS (
                SELECT id
                FROM locations
                WHERE is_active = true
                  AND is_warehouse_location = true
            ),
            serialized_parts AS (
                SELECT
                    'serialized' AS source_type,
                    i.id AS item_id,
                    i.item_code,
                    a.id AS asset_id,
                    a.asset_code,
                    1::numeric AS quantity,
                    l.id AS location_id,
                    l.code AS location_code,
                    l.name AS location_name,
                    l.rack_code,
                    l.shelf_code,
                    l.aisle_id
                FROM assets a
                JOIN items i
                    ON i.id = a.item_id
                JOIN locations l
                    ON l.id = a.current_location_id
                WHERE a.current_location_id IN (
                    SELECT id FROM warehouse_locations
                )
                  AND i.is_active = true
                  AND UPPER(split_part(i.item_code, '-', 1)) IN (
                      SELECT UPPER(prefix)
                      FROM matched_prefixes
                  )
            ),
            stock_parts AS (
                SELECT
                    'stock' AS source_type,
                    i.id AS item_id,
                    i.item_code,
                    NULL::bigint AS asset_id,
                    NULL::text AS asset_code,
                    s.quantity,
                    l.id AS location_id,
                    l.code AS location_code,
                    l.name AS location_name,
                    l.rack_code,
                    l.shelf_code,
                    l.aisle_id
                FROM inventory_stock s
                JOIN items i
                    ON i.id = s.item_id
                JOIN locations l
                    ON l.id = s.location_id
                WHERE s.location_id IN (
                    SELECT id FROM warehouse_locations
                )
                  AND s.quantity > 0
                  AND i.is_active = true
                  AND UPPER(split_part(i.item_code, '-', 1)) IN (
                      SELECT UPPER(prefix)
                      FROM matched_prefixes
                  )
            )
            SELECT *
            FROM serialized_parts

            UNION ALL

            SELECT *
            FROM stock_parts

            ORDER BY location_name, item_code, asset_code NULLS LAST
            """
        ),
        {"device_group_id": device_group["id"]},
    ).mappings().all()

    return WarehouseDeviceGroupPartsOut(
        device_group_id=device_group["id"],
        device_group_code=device_group["code"],
        matched_prefixes=matched_prefixes,
        parts=[WarehouseDeviceGroupPartOut(**dict(row)) for row in rows],
    )

@router.get("/aisles/{aisle_id}/warehouse-parts")
def get_warehouse_parts_by_aisle(
    aisle_id: int,
    device_group_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Devuelve todos los parts/items que están actualmente en un pasillo del almacén.

    Fuentes:
    - Assets serializados: assets.current_location_id
    - Stock no serializado: inventory_stock.location_id

    Filtro opcional:
    - device_group_code=CN235, C295, etc.
    """

    aisle = db.execute(
        text(
            """
            SELECT
                id,
                code,
                name
            FROM aisles
            WHERE id = :aisle_id
              AND is_active = true
            """
        ),
        {
            "aisle_id": aisle_id,
        },
    ).mappings().first()

    if aisle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aisle not found or inactive: {aisle_id}",
        )

    device_group_id: int | None = None
    resolved_device_group_code: str | None = None
    matched_prefixes: list[str] = []

    if device_group_code:
        device_group = db.execute(
            text(
                """
                SELECT
                    id,
                    code
                FROM device_groups
                WHERE UPPER(code) = UPPER(:device_group_code)
                  AND is_active = true
                """
            ),
            {
                "device_group_code": device_group_code.strip(),
            },
        ).mappings().first()

        if device_group is None:
            raise HTTPException(
                status_code=404,
                detail=f"Device group not found or inactive: {device_group_code}",
            )

        device_group_id = int(device_group["id"])
        resolved_device_group_code = str(device_group["code"])

        prefix_rows = db.execute(
            text(
                """
                SELECT code AS prefix
                FROM device_groups
                WHERE id = :device_group_id

                UNION

                SELECT alias_code AS prefix
                FROM device_aliases
                WHERE device_group_id = :device_group_id
                  AND is_active = true

                ORDER BY prefix
                """
            ),
            {
                "device_group_id": device_group_id,
            },
        ).mappings().all()

        matched_prefixes = [
            str(row["prefix"])
            for row in prefix_rows
            if row["prefix"]
        ]

    rows = db.execute(
        text(
            """
            WITH matched_prefixes AS (
                SELECT code AS prefix
                FROM device_groups
                WHERE id = :device_group_id

                UNION

                SELECT alias_code AS prefix
                FROM device_aliases
                WHERE device_group_id = :device_group_id
                  AND is_active = true
            ),
            target_locations AS (
                SELECT
                    l.id,
                    l.code,
                    l.name,
                    l.rack_code,
                    l.shelf_code,
                    l.aisle_id
                FROM locations l
                WHERE l.aisle_id = :aisle_id
                  AND l.is_active = true
                  AND l.is_warehouse_location = true
            ),
            serialized_parts AS (
                SELECT
                    'serialized' AS source_type,
                    i.id AS item_id,
                    i.item_code,
                    a.id AS asset_id,
                    a.asset_code,
                    1::numeric AS quantity,
                    l.id AS location_id,
                    l.code AS location_code,
                    l.name AS location_name,
                    l.rack_code,
                    l.shelf_code,
                    l.aisle_id
                FROM assets a
                JOIN items i
                    ON i.id = a.item_id
                JOIN target_locations l
                    ON l.id = a.current_location_id
                WHERE i.is_active = true
                  AND (
                    :use_device_group_filter = false
                    OR UPPER(split_part(i.item_code, '-', 1)) IN (
                        SELECT UPPER(prefix)
                        FROM matched_prefixes
                    )
                  )
            ),
            stock_parts AS (
                SELECT
                    'stock' AS source_type,
                    i.id AS item_id,
                    i.item_code,
                    NULL::bigint AS asset_id,
                    NULL::text AS asset_code,
                    s.quantity,
                    l.id AS location_id,
                    l.code AS location_code,
                    l.name AS location_name,
                    l.rack_code,
                    l.shelf_code,
                    l.aisle_id
                FROM inventory_stock s
                JOIN items i
                    ON i.id = s.item_id
                JOIN target_locations l
                    ON l.id = s.location_id
                WHERE s.quantity > 0
                  AND i.is_active = true
                  AND (
                    :use_device_group_filter = false
                    OR UPPER(split_part(i.item_code, '-', 1)) IN (
                        SELECT UPPER(prefix)
                        FROM matched_prefixes
                    )
                  )
            )
            SELECT *
            FROM serialized_parts

            UNION ALL

            SELECT *
            FROM stock_parts

            ORDER BY
                rack_code,
                shelf_code,
                item_code,
                asset_code NULLS LAST
            """
        ),
        {
            "aisle_id": aisle_id,
            "device_group_id": device_group_id,
            "use_device_group_filter": device_group_id is not None,
        },
    ).mappings().all()

    return {
        "aisle_id": aisle["id"],
        "aisle_code": aisle["code"],
        "aisle_name": aisle["name"],
        "device_group_code": resolved_device_group_code,
        "matched_prefixes": matched_prefixes,
        "parts": [dict(row) for row in rows],
    }