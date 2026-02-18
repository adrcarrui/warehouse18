import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Request, Body
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/rfid", tags=["rfid"])

# Lista global de subscriptores (colas). MVP: vale.
_subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
_sub_lock = asyncio.Lock()

KEEPALIVE_SECONDS = 15


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def publish_rfid_event(payload: dict[str, Any]) -> None:
    """
    Llama a esto desde tu código RFID cuando tengas un evento que quieres ver en la UI.
    """
    payload = dict(payload)
    payload.setdefault("ts", _now_iso())

    async with _sub_lock:
        dead: list[asyncio.Queue] = []
        for q in _subscribers:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                # Si un cliente no consume, lo dejamos caer (MVP).
                pass
            except Exception:
                dead.append(q)
        for q in dead:
            _subscribers.discard(q)


def _sse(data: dict[str, Any], event: str | None = None) -> bytes:
    """
    Serializa como SSE. (data: <json>\n\n)
    """
    body = ""
    if event:
        body += f"event: {event}\n"
    body += "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"
    return body.encode("utf-8")


@router.get("/events")
async def rfid_events(request: Request):
    """
    SSE stream: /api/rfid/events
    """
    q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=200)

    async with _sub_lock:
        _subscribers.add(q)

    async def gen() -> AsyncGenerator[bytes, None]:
        try:
            # Mensaje inicial (útil para confirmar conexión)
            yield _sse({"ts": _now_iso(), "type": "hello"})

            while True:
                if await request.is_disconnected():
                    break

                try:
                    msg = await asyncio.wait_for(q.get(), timeout=KEEPALIVE_SECONDS)
                    # puedes usar event=msg.get("type") si quieres separar por tipo
                    yield _sse(msg)
                except asyncio.TimeoutError:
                    # keep-alive para que no se cierre por inactividad
                    yield b": keep-alive\n\n"
        finally:
            async with _sub_lock:
                _subscribers.discard(q)

    return StreamingResponse(gen(), media_type="text/event-stream")

@router.post("/emit")
async def emit_test(payload: dict = Body(...)):
    await publish_rfid_event(payload)
    return {"status": "ok"}