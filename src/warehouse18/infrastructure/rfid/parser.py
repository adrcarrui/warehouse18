# src/warehouse18/infrastructure/rfid/parser.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class Frame:
    addr: int
    cmd: int
    data: bytes
    raw: bytes


def decode_frame(frame: bytes) -> Frame:
    """
    frame: A0 | Len | Addr | Cmd | Data... | Check
    """
    if len(frame) < 5:
        raise ValueError("Frame demasiado corto")
    addr = frame[2]
    cmd = frame[3]
    data = frame[4:-1]
    return Frame(addr=addr, cmd=cmd, data=data, raw=frame)


@dataclass(frozen=True)
class TagRead:
    epc: str
    antenna: Optional[int]
    rssi_raw: Optional[int]
    seen_at: datetime
    cmd: int


def _hex(b: bytes) -> str:
    return b.hex().upper()


def try_parse_tag_from_inventory(frame: Frame) -> Optional[TagRead]:
    """
    Parse seguro para inventario:
    Espera layout: FreqAnt(2) + PC(2) + EPC(N) + RSSI(1)
    Solo devuelve TagRead si el EPC tiene una longitud razonable.
    """
    d = frame.data
    # mínimo: 2 + 2 + 1 (EPC mínimo 1 byte) + 1 RSSI = 6
    if len(d) < 6:
        return None

    # EPC_len = total - (FreqAnt2 + PC2 + RSSI1)
    epc_len = len(d) - 5
    if epc_len <= 0:
        return None

    # EPC típico: 12 bytes (96-bit) o 24 bytes (192-bit), etc.
    # Aceptamos múltiplos de 2 bytes y un rango razonable.
    if epc_len % 2 != 0 or not (4 <= epc_len <= 64):
        return None

    freq_ant = int.from_bytes(d[0:2], "big")
    ant_id = freq_ant & 0x03

    epc_bytes = d[4:4 + epc_len]
    rssi = d[4 + epc_len]

    epc = epc_bytes.hex().upper()
    if not epc:
        return None

    return TagRead(
        epc=epc,
        antenna=ant_id,
        rssi_raw=rssi,
        seen_at=datetime.now(timezone.utc),
        cmd=frame.cmd,
    )


def pretty_frame(frame: Frame) -> str:
    """
    Para debug: imprime cmd, addr, len(data), data hex recortado.
    """
    data_hex = _hex(frame.data)
    if len(data_hex) > 80:
        data_hex = data_hex[:80] + "..."
    return f"cmd=0x{frame.cmd:02X} addr=0x{frame.addr:02X} data_len={len(frame.data)} data={data_hex}"
