from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import StockContainer, Movement, MovementType
from warehouse18.presentation.api.schemas import RfidIngestIn

# Si existe en tu proyecto (como en la propuesta):
# from warehouse18.presentation.api.routes.rfid_events import publish_rfid_event
# Si no, ajusta el import al path real.
from warehouse18.presentation.api.routes.rfid_events import publish_rfid_event

router = APIRouter(prefix="/rfid", tags=["rfid"])

# Anti-spam: evita crear movimientos duplicados por lecturas repetidas
COOLDOWN_SECONDS = 3
_last_move_ts: dict[int, datetime] = {}  # stock_container_id -> last movement ts

# Cache simple para no consultar MovementType cada vez
_mt_cache: dict[str, int] = {}  # movement_type_code -> movement_type_id


def normalize_epc(v: str) -> str:
    return v.strip().upper()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_mt_id(db: Session, code: str) -> int:
    """
    Devuelve movement_type_id por code, con caché local.
    """
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
    """
    Publica al SSE sin romper el ingest si falla el stream.
    """
    try:
        await publish_rfid_event(payload)
    except Exception:
        # No hacemos drama: el ingest no debería caer porque el monitor tenga problemas.
        return


@router.post("/ingest")
async def ingest_rfid_event(body: RfidIngestIn, request: Request, db: Session = Depends(get_db)):
    epc = normalize_epc(body.epc)

    # 0) antenna_map cargado en startup (config/antenna_map.json)
    antenna_map = getattr(request.app.state, "antenna_map", None)
    if antenna_map is None:
        return {"status": "ignored", "reason": "antenna_map_not_loaded"}

    port = antenna_map.ports.get(body.antenna)
    if not port:
        return {"status": "ignored", "reason": "antenna_not_mapped", "antenna": body.antenna}

    to_location_id = port.location_id
    now = _utcnow()

    # A) SIEMPRE emitir al monitor (esto es lo que tú quieres ver en RFID Monitor)
    await _safe_publish_event(
        {
            "type": "tag",
            "ts": now.isoformat(),
            "epc": epc,
            "antenna": body.antenna,
            "rssi": body.rssi,
            "logical_name": port.logical_name,
            "to_location_id": to_location_id,
        }
    )

    # B) Feature flag: si está desactivado, no tocar BD (solo monitor)
    settings_svc = getattr(request.app.state, "settings_service", None)
    if settings_svc is not None:
        try:
            create_movements = bool(settings_svc.get_rfid_create_movements(db))
        except Exception:
            # Si hay problema leyendo settings, mejor ser conservador:
            # no generes movimientos “por sorpresa”.
            create_movements = False
    else:
        # Si no hay service, comportamiento por defecto (compatibilidad):
        create_movements = True

    if not create_movements:
        return {
            "status": "ok",
            "reason": "movements_disabled",
            "antenna": body.antenna,
            "logical_name": port.logical_name,
            "epc": epc,
        }

    # 1) buscar stock container por EPC (container_code)
    sc = (
        db.query(StockContainer)
        .filter(
            StockContainer.container_code == epc,
            StockContainer.is_active.is_(True),
        )
        .first()
    )
    if not sc:
        return {"status": "ignored", "reason": "container_not_found", "epc": epc}

    from_location_id = sc.location_id

    # 2) si no cambia ubicación, no hay movimiento
    if from_location_id == to_location_id:
        return {"status": "ok", "reason": "no_change", "stock_container_id": sc.id}

    # 3) cooldown anti-spam
    last = _last_move_ts.get(sc.id)
    if last:
        diff = (now - last).total_seconds()
        if diff < COOLDOWN_SECONDS:
            return {
                "status": "ignored",
                "reason": "cooldown",
                "stock_container_id": sc.id,
                "seconds_since_last": diff,
                "cooldown_seconds": COOLDOWN_SECONDS,
            }

    # 4) resolve movement type por code con caché
    mt_id = _get_mt_id(db, "GT")

    # 5) crear movement + actualizar stock_container.location_id (misma transacción)
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

        # actualiza ubicación actual del contenedor
        sc.location_id = to_location_id

        db.commit()
        db.refresh(mv)

        _last_move_ts[sc.id] = now

        return {
            "status": "ok",
            "movement_id": mv.id,
            "stock_container_id": sc.id,
            "from_location_id": from_location_id,
            "to_location_id": to_location_id,
            "antenna": body.antenna,
            "logical_name": port.logical_name,
            "epc": epc,
        }
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))