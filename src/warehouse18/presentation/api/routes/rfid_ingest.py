from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import StockContainer, Movement, MovementType
from warehouse18.presentation.api.schemas import RfidIngestIn
from warehouse18.presentation.api.routes.rfid_events import publish_rfid_event

router = APIRouter(prefix="/rfid", tags=["rfid"])
logger = logging.getLogger("warehouse18.rfid")

COOLDOWN_SECONDS = 3
_last_move_ts: dict[int, datetime] = {}  # stock_container_id -> last movement ts

_mt_cache: dict[str, int] = {}  # movement_type_code -> movement_type_id


def normalize_epc(v: str) -> str:
    return v.strip().upper()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_mt_id(db: Session, code: str) -> int:
    mt_id = _mt_cache.get(code)
    if mt_id:
        return mt_id

    mt = db.query(MovementType).filter(MovementType.code == code).first()
    if not mt:
        raise HTTPException(
            status_code=409,
            detail=f"MovementType code '{code}' not found. Seed it first.",
        )
    _mt_cache[code] = mt.id
    return mt.id


async def _safe_publish_event(payload: dict[str, Any]) -> None:
    try:
        await publish_rfid_event(payload)
    except Exception:
        # El monitor no debe tumbar el ingest
        return


@router.post("/ingest")
async def ingest_rfid_event(
    body: RfidIngestIn,
    request: Request,
    db: Session = Depends(get_db),
):
    epc = normalize_epc(body.epc)
    now = _utcnow()

    logger.info("RFID INGEST RECEIVED | epc=%s antenna=%s rssi=%s", epc, body.antenna, body.rssi)

    async def _emit_and_return(status: str, reason: str, extra: dict[str, Any] | None = None):
        payload: dict[str, Any] = {
            "type": "tag",
            "ts": now.isoformat(),
            "epc": epc,
            "antenna": body.antenna,
            "rssi": body.rssi,
            "status": status,
            "reason": reason,
        }
        if extra:
            payload.update(extra)

        await _safe_publish_event(payload)

        resp = {"status": status, "reason": reason, "epc": epc, "antenna": body.antenna}
        if extra:
            resp.update(extra)
        return resp

    antenna_map = getattr(request.app.state, "antenna_map", None)
    if antenna_map is None:
        logger.warning("RFID INGEST | antenna_map NOT loaded")
        return await _emit_and_return("ignored", "antenna_map_not_loaded")

    port = antenna_map.ports.get(body.antenna)
    if not port:
        logger.warning("RFID INGEST | antenna_not_mapped | antenna=%s", body.antenna)
        return await _emit_and_return("ignored", "antenna_not_mapped", {"antenna": body.antenna})

    to_location_id = port.location_id
    base_extra = {"logical_name": port.logical_name, "to_location_id": to_location_id}

    # Si más adelante metes flags en app.state.settings_service, aquí lo puedes reactivar.
    # Por ahora: siempre crea movimientos.
    create_movements = True
    if not create_movements:
        return await _emit_and_return("ok", "movements_disabled", base_extra)

    sc = (
        db.query(StockContainer)
        .filter(StockContainer.container_code == epc, StockContainer.is_active.is_(True))
        .first()
    )
    if not sc:
        logger.info("RFID INGEST | container_not_found | epc=%s", epc)
        return await _emit_and_return("ignored", "container_not_found", base_extra)

    from_location_id = sc.location_id
    if from_location_id == to_location_id:
        return await _emit_and_return(
            "ok",
            "no_change",
            {**base_extra, "stock_container_id": sc.id, "from_location_id": from_location_id},
        )

    last = _last_move_ts.get(sc.id)
    if last:
        diff = (now - last).total_seconds()
        if diff < COOLDOWN_SECONDS:
            return await _emit_and_return(
                "ignored",
                "cooldown",
                {
                    **base_extra,
                    "stock_container_id": sc.id,
                    "seconds_since_last": diff,
                    "cooldown_seconds": COOLDOWN_SECONDS,
                },
            )

    mt_id = _get_mt_id(db, "GT")

    try:
        mv = Movement(
            movement_type_id=mt_id,
            item_id=sc.item_id,
            quantity=sc.quantity,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            reference_type="container",
            reference_id=sc.id,
            user_id=None,
            notes=f"RFID ingest ant={body.antenna} rssi={body.rssi} ({port.logical_name})",
        )
        db.add(mv)
        sc.location_id = to_location_id

        db.commit()
        db.refresh(mv)

        _last_move_ts[sc.id] = now

        return await _emit_and_return(
            "ok",
            "movement_created",
            {
                **base_extra,
                "movement_id": mv.id,
                "stock_container_id": sc.id,
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
            },
        )

    except IntegrityError as e:
        db.rollback()
        return await _emit_and_return("ignored", "db_integrity_error", {**base_extra, "detail": str(e.orig)})
    
@router.post("/ingest/batch")
async def ingest_rfid_batch(
    body: dict[str, list[RfidIngestIn]],
    request: Request,
    db: Session = Depends(get_db),
):
    reads = body.get("reads", [])
    out: list[dict[str, Any]] = []

    # Importa tu función actual (si está en el mismo módulo, llama directo)
    for r in reads:
        # reutiliza la lógica existente: llama a ingest_rfid_event(r, request, db)
        # pero ojo: ingest_rfid_event hace commit/rollback por lectura.
        # Para empezar, lo dejamos simple:
        res = await ingest_rfid_event(r, request, db)  # type: ignore
        out.append(res)

    return {"count": len(out), "results": out}