from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Frame:
    addr: int
    cmd: int
    data: bytes
    raw: bytes


def decode_frame(frame: bytes) -> Frame:
    """
    frame = A0 | Len | Addr | Cmd | Data | Check
    """
    if len(frame) < 5:
        raise ValueError("Frame demasiado corto")
    addr = frame[2]
    cmd = frame[3]
    data = frame[4:-1]
    return Frame(addr=addr, cmd=cmd, data=data, raw=frame)


def pretty_frame(frame: Frame) -> str:
    data_hex = frame.data.hex().upper()
    if len(data_hex) > 80:
        data_hex = data_hex[:80] + "..."
    return f"cmd=0x{frame.cmd:02X} addr=0x{frame.addr:02X} data_len={len(frame.data)} data={data_hex}"