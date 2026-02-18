from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from warehouse18.infrastructure import db
from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import StockContainer, Movement, MovementType  # ajusta si tu modelo se llama Movements
# Si MovementType existe y quieres usarlo, luego lo buscamos.

from warehouse18.presentation.api.schemas import RfidIngestIn


router = APIRouter(prefix="/rfid", tags=["rfid"])

# MVP config: antena -> location_id
ANTENNA_TO_LOCATION = {
    0: 1,
    1: 2,
}

# Anti-spam: no crear 200 movements por el mismo contenedor
COOLDOWN_SECONDS = 3
_last_move_ts: dict[int, datetime] = {}  # stock_container_id -> ts


def normalize_epc(v: str) -> str:
    return v.strip().upper()


class RfidIngestIn(BaseModel):
    epc: str
    antenna: int
    rssi: Optional[int] = None
    ts: Optional[str] = None  # opcional


@router.post("/ingest")
def ingest_rfid_event(body: RfidIngestIn, db: Session = Depends(get_db)):
    epc = normalize_epc(body.epc)

    # 1) map antenna -> location
    to_location_id = ANTENNA_TO_LOCATION.get(body.antenna)
    if not to_location_id:
        return {"status": "ignored", "reason": "antenna_not_mapped", "antenna": body.antenna}

    # 2) find stock container by epc
    sc = db.query(StockContainer).filter(StockContainer.container_code == epc, StockContainer.is_active.is_(True)).first()
    if not sc:
        return {"status": "ignored", "reason": "container_not_found", "epc": epc}

    from_location_id = sc.location_id

    # 3) if same location -> nothing
    if from_location_id == to_location_id:
        return {"status": "ok", "reason": "no_change", "stock_container_id": sc.id}

    # 4) cooldown
    now = datetime.now(timezone.utc)
    last = _last_move_ts.get(sc.id)
    if last and (now - last) < timedelta(seconds=COOLDOWN_SECONDS):
        return {"status": "ignored", "reason": "cooldown", "stock_container_id": sc.id}

    print("[ingest] epc=", epc, "antenna=", body.antenna, "to_location_id=", to_location_id, "logical=", port.logical_name)
    print("[ingest] sc.id=", sc.id, "from_location_id=", sc.location_id)

    # 5) create movement + update stock container location
    try:
        mv = Movement(
            movement_type_id=11,  # TODO: pon el ID real "TRANSFER" / "MOVE" que uséis
            stock_container_id=sc.id,
            item_id=sc.item_id,
            quantity=sc.quantity,  # MVP: mover todo lo que hay
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            user_id=None,
            notes=f"RFID ingest ant={body.antenna} rssi={body.rssi}",
        )
        db.add(mv)

        sc.location_id = to_location_id
        print("[ingest] updating sc.location_id ->", to_location_id)

        db.commit()
        db.refresh(mv)

        _last_move_ts[sc.id] = now

        return {"status": "ok", "movement_id": mv.id, "stock_container_id": sc.id}
    except IntegrityError as e:
        db.rollback()
        print("[ingest] IntegrityError:", repr(e.orig))
        raise HTTPException(status_code=409, detail=str(e.orig))
