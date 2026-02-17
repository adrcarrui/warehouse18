# src/warehouse18/infrastructure/rfid/commands.py

from __future__ import annotations


def build_8a_fast_switch_inventory_payload(
    *,
    ants: list[int],           # antenas 1..N (tu caso 16)
    stay_times: list[int] | None = None,  # tiempo por antena (unidades del lector)
    interval_ms: int = 0,
    repeat: int = 0x01,         # número de rondas
) -> bytes:
    """
    Construye el payload del comando 0x8A (Fast Switch Ant Inventory).

    NOTA: La estructura exacta depende del firmware, pero en muchos lectores:
    - Se envía una lista de (ant, stay)
    - interval
    - repeat

    Como tu fabricante te dio doc V3.8, ajustaremos exacto con esa tabla cuando quieras,
    pero de momento lo montamos de forma compatible con lo que ya te funciona.
    """
    if not ants:
        raise ValueError("ants no puede estar vacío")
    if any(a < 1 or a > 16 for a in ants):
        raise ValueError("antena fuera de rango 1..16")

    if stay_times is None:
        stay_times = [1] * len(ants)

    if len(stay_times) != len(ants):
        raise ValueError("stay_times debe tener la misma longitud que ants")

    # Tu trama manual empieza con 0x00 y luego pares 01 01 02 01 03 01...
    # Eso sugiere: 0x00 + (ant, stay)*N + ... + repeat/interval/etc.
    body = bytearray()
    body.append(0x00)

    for ant, st in zip(ants, stay_times):
        body.append(ant & 0xFF)
        body.append(st & 0xFF)

    # Placeholder de parámetros finales (porque tu firmware espera más bytes)
    # Mantengo el patrón “compatible con lo que ya te funciona”.
    # Luego lo alineamos 1:1 con la tabla del doc V3.8.
    body.extend([0x00, 0x05, 0x00, 0x06, 0x00, 0x07, 0x00])
    body.append(repeat & 0xFF)

    return bytes(body)
