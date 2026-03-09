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
    Parse para respuesta 0x8A observado en rfid_simple_test.py.

    Layout de frame.data:
        FreqAnt(1) + PC(2) + EPC(N) + RSSI(1)

    Donde:
      - FreqAnt: 1 byte
      - PC: 2 bytes
      - EPC: longitud variable
      - RSSI: 1 byte final
    """
    d = frame.data
    if frame.cmd != 0x8A:
        return None
    # mínimo: FreqAnt(1) + PC(2) + EPC(1 byte mínimo) + RSSI(1) = 5 bytes
    if len(d) < 5:
        return None

    freq_ant = d[0]
    ant_id = freq_ant & 0x03

    # EPC_len = total - (FreqAnt1 + PC2 + RSSI1)
    epc_len = len(d) - 4
    if epc_len <= 0:
        return None

    epc_bytes = d[3:3 + epc_len]
    rssi = d[3 + epc_len]

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
