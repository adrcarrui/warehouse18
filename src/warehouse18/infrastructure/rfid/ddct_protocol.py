# src/warehouse18/infrastructure/rfid/ddct_protocol.py

from __future__ import annotations

from typing import Iterator

HEAD = 0xA0
PUBLIC_ADDR = 0xFF


def checksum_ddct(frame_wo_checksum: bytes) -> int:
    """
    Checksum DDCT: (~sum(bytes)) + 1, limitado a 1 byte.
    Se calcula sobre todo el frame excepto el checksum final.
    """
    s = sum(frame_wo_checksum) & 0xFF
    return ((~s + 1) & 0xFF)


def build_frame(cmd: int, data: bytes = b"", addr: int = PUBLIC_ADDR) -> bytes:
    """
    Formato: A0 | Len | Addr | Cmd | Data... | Check

    Len incluye: Addr + Cmd + Data + Check
    Total bytes del frame = 2 + Len
    """
    if not (0 <= cmd <= 0xFF):
        raise ValueError("cmd fuera de rango 0..255")
    if not (0 <= addr <= 0xFF):
        raise ValueError("addr fuera de rango 0..255")

    length = 1 + 1 + len(data) + 1  # Addr + Cmd + Data + Check
    body = bytes([addr, cmd]) + data
    frame_wo_chk = bytes([HEAD, length]) + body
    chk = checksum_ddct(frame_wo_chk)
    return frame_wo_chk + bytes([chk])


def expected_total_len(buf: bytes) -> int | None:
    """
    Si buf comienza con HEAD y tiene al menos Len, devuelve total bytes del frame (2 + Len).
    Si no se puede determinar aún, devuelve None.
    """
    if len(buf) < 2:
        return None
    if buf[0] != HEAD:
        return None
    return 2 + buf[1]


def verify_frame(frame: bytes) -> bool:
    if len(frame) < 5:
        return False
    if frame[0] != HEAD:
        return False
    length = frame[1]
    if len(frame) != 2 + length:
        return False
    return checksum_ddct(frame[:-1]) == frame[-1]


def iter_frames_from_bytes(chunks: Iterator[bytes]) -> Iterator[bytes]:
    """
    Reconstruye frames desde un stream de bytes en chunks.
    - Busca HEAD
    - Usa Len para cortar el frame
    - Valida checksum
    - Si checksum falla, re-sincroniza buscando el siguiente HEAD
    """
    buf = bytearray()

    for chunk in chunks:
        if not chunk:
            continue
        buf.extend(chunk)

        while True:
            # Buscar HEAD
            try:
                i = buf.index(HEAD)
            except ValueError:
                buf.clear()
                break

            # tirar basura previa
            if i > 0:
                del buf[:i]

            total = expected_total_len(buf)
            if total is None:
                break
            if len(buf) < total:
                break

            frame = bytes(buf[:total])
            del buf[:total]

            if verify_frame(frame):
                yield frame
            else:
                # checksum malo: seguimos buscando HEAD en lo que quede
                continue
