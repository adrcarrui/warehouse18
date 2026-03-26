#!/usr/bin/env python3
from __future__ import annotations

import argparse
import select
import socket
import sys
import time
from dataclasses import dataclass
from typing import Iterable

HEAD = 0xA0
PUBLIC_ADDR = 0x01  # en tus capturas la app usa 0x01

# Inferido de tus capturas del software del fabricante:
#   A0 04 01 6C 00 EF
#   A0 04 01 6C 10 DF
# No está documentado en el PDF como comando público; aquí lo usamos tal cual
# porque es exactamente lo que tu app envía antes/depués del inventario.
BANK_A_VALUE = 0x00
BANK_B_VALUE = 0x10


def checksum_ddct(frame_wo_checksum: bytes) -> int:
    total = sum(frame_wo_checksum) & 0xFF
    return ((~total + 1) & 0xFF)


def build_frame(cmd: int, data: bytes = b"", addr: int = PUBLIC_ADDR) -> bytes:
    length = 1 + 1 + len(data) + 1  # Addr + Cmd + Data + Check
    frame_wo_chk = bytes([HEAD, length, addr, cmd]) + data
    return frame_wo_chk + bytes([checksum_ddct(frame_wo_chk)])


def verify_frame(frame: bytes) -> bool:
    if len(frame) < 5:
        return False
    if frame[0] != HEAD:
        return False
    if len(frame) != 2 + frame[1]:
        return False
    return checksum_ddct(frame[:-1]) == frame[-1]


def expected_total_len(buf: bytes) -> int | None:
    if len(buf) < 2 or buf[0] != HEAD:
        return None
    return 2 + buf[1]


@dataclass
class ParsedTag:
    epc: str
    antenna_in_bank: int
    physical_antenna: int
    rssi: int | None
    bank_name: str
    raw_frame_hex: str


def iter_frames(sock: socket.socket, window_s: float) -> Iterable[bytes]:
    buf = bytearray()
    end = time.monotonic() + window_s

    while time.monotonic() < end:
        remaining = max(0.0, end - time.monotonic())
        r, _, _ = select.select([sock], [], [], remaining)
        if not r:
            break

        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Socket cerrado por el lector")
        buf.extend(chunk)

        while True:
            try:
                i = buf.index(HEAD)
            except ValueError:
                buf.clear()
                break

            if i > 0:
                del buf[:i]

            total = expected_total_len(buf)
            if total is None or len(buf) < total:
                break

            frame = bytes(buf[:total])
            del buf[:total]

            if verify_frame(frame):
                yield frame


def parse_tag_frame(frame: bytes, bank_offset: int, bank_name: str) -> ParsedTag | None:
    # Respuesta esperada de inventario 0x8A con tag:
    # Head Len Addr Cmd FreqAnt PC EPC RSSI Check
    # La doc dice que el ID de antena va en los bits bajos de FreqAnt.
    if len(frame) < 10:
        return None
    if frame[3] != 0x8A:
        return None

    data = frame[4:-1]
    if len(data) < 5:
        return None

    freq_ant = data[0]
    antenna_in_bank = freq_ant & 0x07  # 0..7 en la variante de 8 antenas

    # EPC = todo salvo FreqAnt(1), PC(2), RSSI(1)
    epc_len = len(data) - 4
    if epc_len <= 0:
        return None

    epc_bytes = data[3:3 + epc_len]
    if not epc_bytes:
        return None

    rssi = data[3 + epc_len] if len(data) > 4 else None
    physical = bank_offset + antenna_in_bank + 1

    return ParsedTag(
        epc=epc_bytes.hex().upper(),
        antenna_in_bank=antenna_in_bank + 1,
        physical_antenna=physical,
        rssi=rssi,
        bank_name=bank_name,
        raw_frame_hex=frame.hex().upper(),
    )


def build_fast_inventory_8ant(addr: int = PUBLIC_ADDR) -> bytes:
    # Esta es exactamente la trama que capturaste de la app del fabricante.
    # A0 15 01 8A 00 01 01 01 02 01 03 01 04 01 05 01 06 01 07 01 00 01 9B
    data = bytes.fromhex("00 01 01 01 02 01 03 01 04 01 05 01 06 01 07 01 00 01")
    return build_frame(0x8A, data=data, addr=addr)


def build_bank_select(bank_value: int, addr: int = PUBLIC_ADDR) -> bytes:
    return build_frame(0x6C, data=bytes([bank_value]), addr=addr)


def send_and_log(sock: socket.socket, frame: bytes, label: str) -> None:
    print(f"SEND {label:<12} {frame.hex().upper()}")
    sock.sendall(frame)


def recv_and_print(sock: socket.socket, window_s: float, bank_offset: int, bank_name: str) -> list[ParsedTag]:
    tags: list[ParsedTag] = []
    for frame in iter_frames(sock, window_s=window_s):
        hex_frame = frame.hex().upper()
        print(f"RECV {bank_name:<12} {hex_frame}")
        parsed = parse_tag_frame(frame, bank_offset=bank_offset, bank_name=bank_name)
        if parsed:
            tags.append(parsed)
    return tags


def main() -> int:
    parser = argparse.ArgumentParser(description="Sondeo simple de antenas RFID por bancos A/B")
    parser.add_argument("--host", default="192.168.0.101")
    parser.add_argument("--port", type=int, default=4001)
    parser.add_argument("--addr", type=lambda x: int(x, 0), default=0x01, help="Dirección del lector, por ejemplo 0x01")
    parser.add_argument("--loops", type=int, default=20, help="Número de ciclos A->B")
    parser.add_argument("--recv-window", type=float, default=0.35, help="Ventana de recepción tras cada inventario")
    parser.add_argument("--pause", type=float, default=0.05, help="Pausa pequeña entre comandos")
    args = parser.parse_args()

    inventory = build_fast_inventory_8ant(addr=args.addr)
    bank_a = build_bank_select(BANK_A_VALUE, addr=args.addr)
    bank_b = build_bank_select(BANK_B_VALUE, addr=args.addr)

    seen: set[tuple[str, int]] = set()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(3.0)
        sock.connect((args.host, args.port))
        sock.settimeout(None)

        print(f"Conectado a {args.host}:{args.port} addr=0x{args.addr:02X}")
        print("Pulsa Ctrl+C para salir. Sí, la vida moderna es esto.\n")

        try:
            for i in range(args.loops):
                print(f"\n--- CICLO {i + 1}/{args.loops} ---")

                # Banco A: inferido como antenas físicas 1..8
                send_and_log(sock, bank_a, "BANK_A")
                time.sleep(args.pause)
                send_and_log(sock, inventory, "INV_A")
                tags_a = recv_and_print(sock, args.recv_window, bank_offset=0, bank_name="BANK_A")

                # Banco B: inferido como antenas físicas 9..16
                send_and_log(sock, bank_b, "BANK_B")
                time.sleep(args.pause)
                send_and_log(sock, inventory, "INV_B")
                tags_b = recv_and_print(sock, args.recv_window, bank_offset=8, bank_name="BANK_B")

                tags = tags_a + tags_b
                if not tags:
                    print("Sin tags en este ciclo")
                    continue

                for tag in tags:
                    key = (tag.epc, tag.physical_antenna)
                    new_marker = "NEW" if key not in seen else "   "
                    seen.add(key)
                    print(
                        f"{new_marker} TAG epc={tag.epc} bank={tag.bank_name} "
                        f"ant_in_bank={tag.antenna_in_bank} physical_ant={tag.physical_antenna} "
                        f"rssi={tag.rssi}"
                    )
        except KeyboardInterrupt:
            print("\nFin por teclado")

    print("\nResumen final:")
    if not seen:
        print("No se detectó ningún EPC")
    else:
        for epc, ant in sorted(seen, key=lambda x: (x[1], x[0])):
            print(f"- EPC {epc} visto en antena física {ant}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
