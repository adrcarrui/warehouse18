from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from warehouse18.application.rfid.door_engine import RFIDEvent, process_event
from warehouse18.infrastructure.db import get_db

router = APIRouter(prefix="/rfid", tags=["rfid"])


class RFIDIngestIn(BaseModel):
    epc: str
    antenna: int
    rssi: float | None = None
    reader_id: str = "reader-1"


@router.post("/ingest")
def rfid_ingest(payload: RFIDIngestIn, db: Session = Depends(get_db)):
    event = RFIDEvent(
        epc=payload.epc,
        antenna=payload.antenna,
        reader_id=payload.reader_id,
        rssi=payload.rssi,
    )
    return process_event(db=db, event=event)