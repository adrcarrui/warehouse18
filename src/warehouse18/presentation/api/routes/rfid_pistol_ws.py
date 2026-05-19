# src/warehouse18/presentation/api/routes/rfid_pistol_ws.py
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from warehouse18.presentation.api.ws_manager import ws_manager

router = APIRouter(prefix="/rfid/pistol", tags=["rfid-pistol"])


@router.websocket("/ws/{device_id}")
async def pistol_ws(websocket: WebSocket, device_id: str):
    await ws_manager.connect(device_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            msg_type = data.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "ack":
                print(f"[pistol:{device_id}] ACK -> {data}")
            elif msg_type == "search_result":
                print(f"[pistol:{device_id}] SEARCH RESULT -> {data}")
            elif msg_type == "write_result":
                print(f"[pistol:{device_id}] WRITE RESULT -> {data}")
            else:
                print(f"[pistol:{device_id}] MESSAGE -> {data}")

    except WebSocketDisconnect:
        await ws_manager.disconnect(device_id)
    except Exception as e:
        print(f"[pistol:{device_id}] websocket error: {e}")
        await ws_manager.disconnect(device_id)