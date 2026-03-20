from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from warehouse18.application.rfid.door_engine import RFIDEvent, process_event
from warehouse18.infrastructure.db import get_db
from warehouse18.presentation.api.security import require_rfid_api_key

log = logging.getLogger("warehouse18.rfid.ingest")

router = APIRouter(prefix="/rfid", tags=["rfid"])


class RFIDIngestIn(BaseModel):
    epc: str
    antenna: int
    rssi: float | None = None
    reader_id: str = "reader-1"


@router.post("/ingest")
def rfid_ingest(
    payload: RFIDIngestIn,
    _: None = Depends(require_rfid_api_key),
    db: Session = Depends(get_db),
):
    log.info(
        "INGEST START epc=%s antenna=%s reader_id=%s rssi=%s",
        payload.epc,
        payload.antenna,
        payload.reader_id,
        payload.rssi,
    )

    event = RFIDEvent(
        epc=payload.epc,
        antenna=payload.antenna,
        reader_id=payload.reader_id,
        rssi=payload.rssi,
    )

    log.info(
        "INGEST BEFORE process_event epc=%s antenna=%s reader_id=%s",
        event.epc,
        event.antenna,
        event.reader_id,
    )

    result = process_event(db=db, event=event)

    log.info(
        "INGEST AFTER process_event epc=%s antenna=%s result=%r",
        event.epc,
        event.antenna,
        result,
    )

    return result