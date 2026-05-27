from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db


router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    message: str
    severity: str
    status: str
    source: str

    entity_type: str | None = None
    entity_id: str | None = None

    movement_id: int | None = None
    item_id: int | None = None
    epc: str | None = None

    created_at: datetime
    updated_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    metadata: dict[str, Any] | None = None


@router.get("", response_model=list[AlertOut])
def list_alerts(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    source: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[AlertOut]:
    rows = db.execute(
        text("""
            SELECT
                id,
                code,
                title,
                message,
                severity,
                status,
                source,
                entity_type,
                entity_id,
                movement_id,
                item_id,
                epc,
                created_at,
                updated_at,
                acknowledged_at,
                resolved_at,
                metadata
            FROM alerts
            WHERE (
                CAST(:status AS TEXT) IS NULL
                OR status = CAST(:status AS TEXT)
            )
            AND (
                CAST(:severity AS TEXT) IS NULL
                OR severity = CAST(:severity AS TEXT)
            )
            AND (
                CAST(:source AS TEXT) IS NULL
                OR source = CAST(:source AS TEXT)
            )
            ORDER BY
                CASE
                    WHEN status = 'open' THEN 0
                    WHEN status = 'acknowledged' THEN 1
                    WHEN status = 'resolved' THEN 2
                    WHEN status = 'dismissed' THEN 3
                    ELSE 4
                END,
                CASE
                    WHEN severity = 'critical' THEN 0
                    WHEN severity = 'warning' THEN 1
                    WHEN severity = 'info' THEN 2
                    ELSE 3
                END,
                created_at DESC
            LIMIT :limit
        """),
        {
            "status": status,
            "severity": severity,
            "source": source,
            "limit": limit,
        },
    ).mappings().all()

    return [AlertOut(**dict(row)) for row in rows]


@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
) -> AlertOut:
    row = db.execute(
        text("""
            UPDATE alerts
            SET
                status = 'acknowledged',
                acknowledged_at = COALESCE(acknowledged_at, now()),
                updated_at = now()
            WHERE id = :alert_id
              AND status = 'open'
            RETURNING
                id,
                code,
                title,
                message,
                severity,
                status,
                source,
                entity_type,
                entity_id,
                movement_id,
                item_id,
                epc,
                created_at,
                updated_at,
                acknowledged_at,
                resolved_at,
                metadata
        """),
        {
            "alert_id": alert_id,
        },
    ).mappings().first()

    if row is None:
        row = db.execute(
            text("""
                SELECT
                    id,
                    code,
                    title,
                    message,
                    severity,
                    status,
                    source,
                    entity_type,
                    entity_id,
                    movement_id,
                    item_id,
                    epc,
                    created_at,
                    updated_at,
                    acknowledged_at,
                    resolved_at,
                    metadata
                FROM alerts
                WHERE id = :alert_id
            """),
            {
                "alert_id": alert_id,
            },
        ).mappings().first()

    db.commit()

    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertOut(**dict(row))


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
) -> AlertOut:
    row = db.execute(
        text("""
            UPDATE alerts
            SET
                status = 'resolved',
                resolved_at = COALESCE(resolved_at, now()),
                updated_at = now()
            WHERE id = :alert_id
              AND status IN ('open', 'acknowledged')
            RETURNING
                id,
                code,
                title,
                message,
                severity,
                status,
                source,
                entity_type,
                entity_id,
                movement_id,
                item_id,
                epc,
                created_at,
                updated_at,
                acknowledged_at,
                resolved_at,
                metadata
        """),
        {
            "alert_id": alert_id,
        },
    ).mappings().first()

    if row is None:
        row = db.execute(
            text("""
                SELECT
                    id,
                    code,
                    title,
                    message,
                    severity,
                    status,
                    source,
                    entity_type,
                    entity_id,
                    movement_id,
                    item_id,
                    epc,
                    created_at,
                    updated_at,
                    acknowledged_at,
                    resolved_at,
                    metadata
                FROM alerts
                WHERE id = :alert_id
            """),
            {
                "alert_id": alert_id,
            },
        ).mappings().first()

    db.commit()

    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertOut(**dict(row))