# src/warehouse18/presentation/api/ws_manager.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from typing import Dict, Optional
import asyncio


router = APIRouter(prefix="/ws_manager", tags=["ws_manager"])

class DeviceConnectionManager:
    def __init__(self) -> None:
        self._devices: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, device_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._devices[device_id] = websocket

    async def disconnect(self, device_id: str) -> None:
        async with self._lock:
            self._devices.pop(device_id, None)

    async def send_to_device(self, device_id: str, payload: dict) -> bool:
        async with self._lock:
            ws: Optional[WebSocket] = self._devices.get(device_id)

        if ws is None:
            return False

        try:
            await ws.send_json(payload)
            return True
        except Exception:
            async with self._lock:
                self._devices.pop(device_id, None)
            return False

    async def broadcast(self, payload: dict) -> None:
        async with self._lock:
            items = list(self._devices.items())

        to_remove = []
        for device_id, ws in items:
            try:
                await ws.send_json(payload)
            except Exception:
                to_remove.append(device_id)

        if to_remove:
            async with self._lock:
                for device_id in to_remove:
                    self._devices.pop(device_id, None)

    async def is_connected(self, device_id: str) -> bool:
        async with self._lock:
            return device_id in self._devices


ws_manager = DeviceConnectionManager()