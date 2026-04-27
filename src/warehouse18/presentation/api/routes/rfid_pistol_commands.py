# src/warehouse18/presentation/api/routes/rfid_pistol_commands.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional

from warehouse18.presentation.api.ws_manager import ws_manager

router = APIRouter(prefix="/api/rfid/pistol", tags=["rfid-pistol"])


class SendTargetEpcIn(BaseModel):
    device_id: str = Field(..., min_length=1)
    epc: str = Field(..., min_length=1)
    mode: Literal["search", "write"] = "search"
    item_key: Optional[str] = None


@router.post("/send-target-epc")
async def send_target_epc(payload: SendTargetEpcIn):
    message = {
        "type": "target_epc",
        "mode": payload.mode,
        "epc": payload.epc,
        "itemKey": payload.item_key,
    }

    sent = await ws_manager.send_to_device(payload.device_id, message)
    if not sent:
        raise HTTPException(status_code=404, detail="Pistola no conectada")

    return {
        "ok": True,
        "device_id": payload.device_id,
        "message": message,
    }