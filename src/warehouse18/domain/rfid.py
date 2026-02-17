# src/warehouse18/domain/rfid.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def normalize_epc(epc: str) -> str:
    """
    Normaliza EPC a un formato consistente:
    - quita espacios y saltos
    - uppercase
    - valida que sea hexadecimal (si no, revienta con ValueError)
    """
    e = epc.strip().replace(" ", "").upper()
    if not e:
        raise ValueError("EPC vacío")
    # Validación hex simple
    try:
        bytes.fromhex(e)
    except ValueError as ex:
        raise ValueError(f"EPC no es hexadecimal válido: {epc!r}") from ex
    return e


@dataclass(frozen=True)
class RFIDReadEvent:
    """
    Evento de lectura RFID normalizado (transitorio).
    No es una entidad de BD: se genera, se publica y (opcionalmente) se persiste como log en otro lado.
    """
    epc: str
    reader_id: str
    antenna: Optional[int]
    rssi: Optional[float]
    seen_at: datetime
    protocol: Optional[str] = None
    raw: Optional[str] = None  # hex string o texto para debug

    def __post_init__(self) -> None:
        object.__setattr__(self, "epc", normalize_epc(self.epc))
        if not self.reader_id or not self.reader_id.strip():
            raise ValueError("reader_id es obligatorio")

        if self.antenna is not None and self.antenna < 0:
            raise ValueError("antenna no puede ser negativa")

    def to_dict(self) -> dict:
        """
        Serialización simple (útil para SSE/JSON).
        """
        return {
            "epc": self.epc,
            "reader_id": self.reader_id,
            "antenna": self.antenna,
            "rssi": self.rssi,
            "seen_at": self.seen_at.isoformat(),
            "protocol": self.protocol,
            "raw": self.raw,
        }


@dataclass(frozen=True)
class ReaderStatusEvent:
    """
    Evento opcional: estado del lector (conectado/desconectado/error).
    Útil para UI/monitorización.
    """
    reader_id: str
    status: str  # "connected" | "disconnected" | "error"
    at: datetime
    message: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.reader_id or not self.reader_id.strip():
            raise ValueError("reader_id es obligatorio")
        if self.status not in {"connected", "disconnected", "error"}:
            raise ValueError("status inválido")

    def to_dict(self) -> dict:
        return {
            "reader_id": self.reader_id,
            "status": self.status,
            "at": self.at.isoformat(),
            "message": self.message,
        }
