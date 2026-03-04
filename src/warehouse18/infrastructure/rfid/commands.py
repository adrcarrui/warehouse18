# src/warehouse18/infrastructure/rfid/commands.py
from __future__ import annotations

import os


def build_8a_fast_switch_inventory_payload(
    *,
    ants: list[int],                 # antenas 1..N
    stay_times: list[int] | None = None,
    repeat: int = 0x01,
) -> bytes:
    """
    Payload 0x8A compatible con la trama que te funciona en rfid_simple_test.py:
    00 + (ant, stay)*N + TAIL

    TAIL por defecto: 000500060007000501  (igual que tu script)
    """
    if not ants:
        raise ValueError("ants no puede estar vacío")
    if any(a < 1 or a > 16 for a in ants):
        raise ValueError("antena fuera de rango 1..16")

    if stay_times is None:
        stay_times = [1] * len(ants)
    if len(stay_times) != len(ants):
        raise ValueError("stay_times debe tener la misma longitud que ants")

    tail_hex = os.getenv("WAREHOUSE18_RFID_8A_TAIL_HEX", "000500060007000501").strip().replace(" ", "")
    tail = bytes.fromhex(tail_hex)

    body = bytearray()
    body.append(0x00)
    for ant, st in zip(ants, stay_times):
        body.append(ant & 0xFF)
        body.append(st & 0xFF)

    # Si el tail incluye repeat dentro, perfecto. Si no, lo añadimos.
    # (Tu tail por defecto ya acaba en ...01)
    if len(tail) > 0:
        body.extend(tail)
    else:
        body.append(repeat & 0xFF)

    return bytes(body)