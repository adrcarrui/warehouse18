from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from warehouse18.domain.models.rfid_event_log import RfidEventLog
from warehouse18.domain.models.user import User
from warehouse18.infrastructure.db import get_db
from warehouse18.presentation.api.schemas import RFIDEventReviewIn
from warehouse18.presentation.api.security import require_rfid_api_key

router = APIRouter(prefix="/rfid", tags=["RFID Events"])

_subscribers: set[asyncio.Queue[dict]] = set()
_sub_lock = asyncio.Lock()
KEEPALIVE_SECONDS = 15


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sse(data: dict, event: str | None = None) -> bytes:
    body = ""
    if event:
        body += f"event: {event}\n"
    body += "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"
    return body.encode("utf-8")


async def publish_rfid_event(payload: dict) -> None:
    payload = dict(payload)
    payload.setdefault("ts", _now_iso())

    async with _sub_lock:
        dead: list[asyncio.Queue] = []

        for q in _subscribers:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass
            except Exception:
                dead.append(q)

        for q in dead:
            _subscribers.discard(q)


@router.get("/events")
async def rfid_events_stream(request: Request):
    q: asyncio.Queue[dict] = asyncio.Queue(maxsize=200)

    async with _sub_lock:
        _subscribers.add(q)

    async def gen():
        try:
            yield _sse({"ts": _now_iso(), "type": "hello"})
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=KEEPALIVE_SECONDS)
                    yield _sse(msg)
                except asyncio.TimeoutError:
                    yield b": keep-alive\n\n"
        finally:
            async with _sub_lock:
                _subscribers.discard(q)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/events/history")
def get_rfid_event_history(
    limit: int = Query(100, ge=1, le=1000),
    door_id: Optional[str] = None,
    epc: Optional[str] = None,
    review_status: Optional[str] = None,
    has_movement: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(RfidEventLog)

    if door_id:
        q = q.filter(RfidEventLog.door_id == door_id)

    if epc:
        q = q.filter(RfidEventLog.epc == epc)

    if review_status:
        q = q.filter(RfidEventLog.review_status == review_status)

    if has_movement is True:
        q = q.filter(RfidEventLog.movement_id.isnot(None))
    elif has_movement is False:
        q = q.filter(RfidEventLog.movement_id.is_(None))

    rows = q.order_by(RfidEventLog.seen_at.desc(), RfidEventLog.id.desc()).limit(limit).all()

    return [
        {
            "id": r.id,
            "event_type": r.event_type,
            "reason": r.reason,
            "epc": r.epc,
            "reader_id": r.reader_id,
            "antenna": r.antenna,
            "door_id": r.door_id,
            "zone_id": r.zone_id,
            "zone_role": r.zone_role,
            "movement_code": r.movement_code,
            "movement_id": r.movement_id,
            "user_id": r.user_id,
            "mysim_user_id": r.mysim_user_id,
            "payload": r.payload_json,
            "created_at": r.created_at,
            "seen_at": r.seen_at,
            "review_status": r.review_status,
            "review_note": r.review_note,
            "reviewed_at": r.reviewed_at,
            "reviewed_by_user_id": r.reviewed_by_user_id,
        }
        for r in rows
    ]


@router.post("/events/{event_id}/confirm")
def confirm_rfid_event(
    event_id: int,
    body: RFIDEventReviewIn,
    _: None = Depends(require_rfid_api_key),
    db: Session = Depends(get_db),
):
    reviewer = db.query(User).filter(User.id == body.reviewed_by_user_id).first()
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer user not found")

    row = db.query(RfidEventLog).filter(RfidEventLog.id == event_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="RFID event not found")

    row.review_status = "confirmed"
    row.reviewed_at = datetime.now(timezone.utc)
    row.reviewed_by_user_id = body.reviewed_by_user_id
    row.review_note = body.note

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "ok": True,
        "event_id": row.id,
        "review_status": row.review_status,
        "reviewed_at": row.reviewed_at,
        "reviewed_by_user_id": row.reviewed_by_user_id,
    }


@router.post("/events/{event_id}/reject")
def reject_rfid_event(
    event_id: int,
    body: RFIDEventReviewIn,
    _: None = Depends(require_rfid_api_key),
    db: Session = Depends(get_db),
):
    reviewer = db.query(User).filter(User.id == body.reviewed_by_user_id).first()
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer user not found")

    row = db.query(RfidEventLog).filter(RfidEventLog.id == event_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="RFID event not found")

    row.review_status = "rejected"
    row.reviewed_at = datetime.now(timezone.utc)
    row.reviewed_by_user_id = body.reviewed_by_user_id
    row.review_note = body.note

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "ok": True,
        "event_id": row.id,
        "review_status": row.review_status,
        "reviewed_at": row.reviewed_at,
        "reviewed_by_user_id": row.reviewed_by_user_id,
    }