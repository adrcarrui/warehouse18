from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import StockContainer, Movement, MovementType
from warehouse18.presentation.api.schemas import RfidIngestIn

router = APIRouter(prefix="/rfid", tags=["rfid"])

# Anti-spam: evita crear movimientos duplicados por lecturas repetidas
COOLDOWN_SECONDS = 3
_last_move_ts: dict[int, datetime] = {}  # stock_container_id -> last movement ts


def normalize_epc(v: str) -> str:
    return v.strip().upper()


@router.post("/ingest")
def ingest_rfid_event(body: RfidIngestIn, request: Request, db: Session = Depends(get_db)):
    epc = normalize_epc(body.epc)

    # 0) antenna_map cargado en startup (config/antenna_map.json)
    antenna_map = getattr(request.app.state, "antenna_map", None)
    if antenna_map is None:
        return {"status": "ignored", "reason": "antenna_map_not_loaded"}

    port = antenna_map.ports.get(body.antenna)
    if not port:
        return {"status": "ignored", "reason": "antenna_not_mapped", "antenna": body.antenna}

    to_location_id = port.location_id

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
    now = datetime.now(timezone.utc)
    last = _last_move_ts.get(sc.id)
    #if last and (now - last) < timedelta(seconds=COOLDOWN_SECONDS):
    #    return {"status": "ignored", "reason": "cooldown", "stock_container_id": sc.id}
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
    # 4) resolve movement type por code (evita hardcode y fallos FK)
    mt = db.query(MovementType).filter(MovementType.code == "GT").first()
    if not mt:
        raise HTTPException(
            status_code=409,
            detail="MovementType code 'GT' not found. Seed it first.",
        )

    # 5) crear movement + actualizar stock_container.location_id (misma transacción)
    try:
        mv = Movement(
            movement_type_id=mt.id,
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
