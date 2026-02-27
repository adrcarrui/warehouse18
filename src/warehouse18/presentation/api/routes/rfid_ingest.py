from __future__ import annotations
import logging
logger = logging.getLogger("warehouse18.rfid")

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
        # El monitor no debe tumbar el ingest.
        return


@router.post("/ingest")
async def ingest_rfid_event(
    body: RfidIngestIn,
    request: Request,
    db: Session = Depends(get_db),
):
    epc = normalize_epc(body.epc)
    now = _utcnow()
    logger.info(
        "RFID INGEST RECEIVED | epc=%s antenna=%s rssi=%s",
        epc,
        body.antenna,
        body.rssi,
    )

    # Helper: publica SIEMPRE al SSE y devuelve la respuesta
    async def _emit_and_return(status: str, reason: str, extra: dict[str, Any] | None = None):
        payload: dict[str, Any] = {
            "type": "tag",                   # lo que escucha la UI
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

    # 0) antenna_map cargado en startup
    antenna_map = getattr(request.app.state, "antenna_map", None)
    if antenna_map is None:
        logger.warning("RFID INGEST | antenna_map NOT loaded")
        return await _emit_and_return("ignored", "antenna_map_not_loaded")

    port = antenna_map.ports.get(body.antenna)
    if not port:
        logger.warning(
        "RFID INGEST | antenna_not_mapped | antenna=%s", body.antenna,)
        return await _emit_and_return(
            "ignored",
            "antenna_not_mapped",
            {"antenna": body.antenna},
        )

    to_location_id = port.location_id

    # Enriquecer SIEMPRE el evento con info de mapeo (esto ayuda mucho a depurar)
    base_extra = {
        "logical_name": port.logical_name,
        "to_location_id": to_location_id,
    }

    # A) Feature flag: si está desactivado, no tocar BD (solo monitor)
    settings_svc = getattr(request.app.state, "settings_service", None)
    if settings_svc is not None:
        try:
            create_movements = bool(settings_svc.get_rfid_create_movements(db))
        except Exception:
            create_movements = False
    else:
        create_movements = True

    if not create_movements:
        return await _emit_and_return("ok", "movements_disabled", base_extra)

    # 1) buscar stock container por EPC
    sc = (
        db.query(StockContainer)
        .filter(
            StockContainer.container_code == epc,
            StockContainer.is_active.is_(True),
        )
        .first()
    )
    if not sc:
        logger.info("RFID INGEST | container_not_found | epc=%s", epc,)
        return await _emit_and_return("ignored", "container_not_found", base_extra)

    from_location_id = sc.location_id

    # 2) si no cambia ubicación, no hay movimiento
    if from_location_id == to_location_id:
        return await _emit_and_return(
            "ok",
            "no_change",
            {**base_extra, "stock_container_id": sc.id, "from_location_id": from_location_id},
        )

    # 3) cooldown anti-spam
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

    # 4) resolve movement type
    mt_id = _get_mt_id(db, "GT")

    # 5) crear movement + actualizar stock_container.location_id
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
        logger.info(
            "RFID MOVE CREATED | movement_id=%s container=%s from=%s to=%s",
            mv.id,
            sc.id,
            from_location_id,
            to_location_id,
        )
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
        # También emitimos el fallo al monitor
        return await _emit_and_return(
            "ignored",
            "db_integrity_error",
            {**base_extra, "detail": str(e.orig)},
        )