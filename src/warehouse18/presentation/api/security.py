from __future__ import annotations

from fastapi import Header, HTTPException, status

from warehouse18.config import settings


def require_rfid_api_key(x_rfid_key: str | None = Header(default=None)) -> None:
    expected = (settings.rfid_api_key or "").strip()

    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RFID API key is not configured",
        )

    if x_rfid_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-RFID-KEY",
        )