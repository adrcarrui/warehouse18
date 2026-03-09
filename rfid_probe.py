from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Optional


# =========================
# Config
# =========================
HOST = "192.168.0.101"
PORT = 4001

# Payload que ya te funcionaba en _dev_test_tcp.py (data del cmd 0x8A)
PAYLOAD_8A_HEX = "000101010201030104000500060007000501"

POLL_INTERVAL_S = 0.20      # cada cuánto pedimos inventario
RECV_WINDOW_S = 1.2         # cuánto tiempo escuchamos después de pedir inventario
SOCKET_TIMEOUT_S = 2.0      # timeout corto para recv


# =========================
# DDCT framing (A0 LEN ...)
# =========================
HEAD = 0xA0


def build_frame(addr: int, cmd: int, data: bytes) -> bytes:
    """
    Frame: A0 LEN ADDR CMD DATA... CHK
    LEN = bytes(ADDR+CMD+DATA+CHK)
    CHK = two's complement of sum(LEN..DATA)
    """
    body = bytes([addr, cmd]) + data
    length = len(body) + 1  # + chk
    frame_wo_chk = bytes([HEAD, length]) + body
    chk = (256 - (sum(frame_wo_chk) % 256)) % 256
    return frame_wo_chk + bytes([chk])


def split_frames(buf: bytearray) -> list[bytes]:
    frames: list[bytes] = []
    while True:
        # buscar 0xA0
        try:
            i = buf.index(HEAD)
        except ValueError:
            buf.clear()
            break
        if i > 0:
            del buf[:i]

        if len(buf) < 2:
            break

        length = buf[1]
        total = 2 + length  # A0 + LEN + length bytes
        if len(buf) < total:
            break

        fr = bytes(buf[:total])
        del buf[:total]
        frames.append(fr)
    return frames


@dataclass
class ParsedFrame:
    addr: int
    cmd: int
    data: bytes
    raw: bytes


def decode_frame(raw: bytes) -> ParsedFrame:
    if len(raw) < 5:
        raise ValueError("frame too short")
    addr = raw[2]
    cmd = raw[3]
    data = raw[4:-1]
    return ParsedFrame(addr=addr, cmd=cmd, data=data, raw=raw)


def try_extract_epc_any(frame: ParsedFrame) -> Optional[str]:
    """
    Best-effort para ver EPC aunque no sepamos el layout exacto.
    - Si data parece un EPC directo (8..64 bytes y par): lo devolvemos.
    - Si data parece layout clásico: FreqAnt(2)+PC(2)+EPC+RSSI: también.
    """
    d = frame.data

    # Layout clásico mínimo
    if len(d) >= 6:
        epc_len = len(d) - 5
        if epc_len > 0 and epc_len % 2 == 0 and 4 <= epc_len <= 64:
            epc_bytes = d[4 : 4 + epc_len]
            return epc_bytes.hex().upper()

    # EPC directo
    if 8 <= len(d) <= 64 and (len(d) % 2 == 0):
        return d.hex().upper()

    return None


def main() -> None:
    inv_payload = bytes.fromhex(PAYLOAD_8A_HEX)
    
    frame = build_frame(addr=0x01, cmd=0x8A, data=inv_payload)
    print("PAYLOAD_8A_HEX:", frame.hex().upper())
    print(f"[CFG] reader={HOST}:{PORT}")
    print(f"[CFG] 8A payload={PAYLOAD_8A_HEX}")
    print("Acerca una tag a la antena... (Ctrl+C para salir)")

    try:
        while True:
            rx = bytearray()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((HOST, PORT))
                s.sendall(frame)

                try:
                    chunk = s.recv(4096)
                    if chunk:
                        rx.extend(chunk)
                except socket.timeout:
                    pass

            frames = split_frames(rx)

            if frames:
                for raw in frames:
                    fr = decode_frame(raw)
                    print(
                        f"[FRAME] cmd=0x{fr.cmd:02X} data_len={len(fr.data)} "
                        f"data={fr.data.hex().upper()} raw={raw.hex().upper()}"
                    )

                    if fr.cmd != 0x8A:
                        continue

                    epc = try_extract_epc_any(fr)
                    if epc:
                        print(f"[TAG] EPC={epc}")
                    else:
                        print("[8A] Frame recibido pero no pude extraer EPC")
            else:
                print("[...] no frames")

            time.sleep(POLL_INTERVAL_S)

    except KeyboardInterrupt:
        print("\nSaliendo...")


if __name__ == "__main__":
    main()