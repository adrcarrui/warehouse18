from __future__ import annotations

import os


def _hexbyte_env(name: str, default_hex: str) -> int:
    v = os.getenv(name, default_hex).strip().upper().replace(" ", "")
    if v.startswith("0X"):
        v = v[2:]
    return int(v, 16)


def _hexbytes_env(name: str, default_hex: str) -> bytes:
    v = os.getenv(name, default_hex).strip().upper().replace(" ", "")
    if v.startswith("0X"):
        v = v[2:]
    return bytes.fromhex(v)


def _int_env(name: str, default: int) -> int:
    v = os.getenv(name)
    return int(v) if v is not None and v.strip() != "" else default


class RfidSettings:
    # --------------------------------------------------
    # EPC / formato de tags
    # --------------------------------------------------
    ITC_MARKER: bytes = _hexbytes_env("WAREHOUSE18_RFID_ITC_MARKER", "17C0")
    TYPE_USER: int = _hexbyte_env("WAREHOUSE18_RFID_TYPE_USER", "01")
    TYPE_ITEM: int = _hexbyte_env("WAREHOUSE18_RFID_TYPE_ITEM", "02")

    # --------------------------------------------------
    # Antenas / zonas legacy
    # --------------------------------------------------
    ZONE_DOOR_ANT: int = _int_env("WAREHOUSE18_RFID_ZONE_DOOR_ANT", 0)
    ZONE_AISLE1_ANT: int = _int_env("WAREHOUSE18_RFID_ZONE_AISLE1_ANT", 1)
    ZONE_AISLE2_ANT: int = _int_env("WAREHOUSE18_RFID_ZONE_AISLE2_ANT", 2)

    # --------------------------------------------------
    # Usuario / presencia
    # --------------------------------------------------
    USER_BIND_TTL_SECONDS: int = _int_env("WAREHOUSE18_RFID_USER_BIND_TTL_SECONDS", 20)
    USER_PRESENCE_TTL_SECONDS: int = _int_env("WAREHOUSE18_RFID_USER_PRESENCE_TTL_SECONDS", 600)
    USER_MIN_RSSI: int = _int_env("WAREHOUSE18_RFID_USER_MIN_RSSI", 0)

    # --------------------------------------------------
    # Modo de routing RFID
    # direct: comportamiento normal/simple
    # dummy_door: demo puerta A/B con cruce
    # --------------------------------------------------
    ROUTE_MODE: str = os.getenv("WAREHOUSE18_RFID_ROUTE_MODE", "direct").strip().lower()

    # --------------------------------------------------
    # Demo puerta 2 antenas
    # --------------------------------------------------
    DEMO_DOOR_ID: str = os.getenv("WAREHOUSE18_RFID_DEMO_DOOR_ID", "door_demo_1").strip()
    DEMO_ANTENNA_A: int = _int_env("WAREHOUSE18_RFID_DEMO_ANTENNA_A", 1)
    DEMO_ANTENNA_B: int = _int_env("WAREHOUSE18_RFID_DEMO_ANTENNA_B", 2)

    DEMO_CROSS_WINDOW_SECONDS: int = _int_env("WAREHOUSE18_RFID_DEMO_CROSS_WINDOW_SECONDS", 10)
    DEMO_MOVE_COOLDOWN_SECONDS: int = _int_env("WAREHOUSE18_RFID_DEMO_MOVE_COOLDOWN_SECONDS", 3)

    DEMO_MOVEMENT_A_TO_B: str = os.getenv(
        "WAREHOUSE18_RFID_DEMO_MOVEMENT_A_TO_B",
        "GI",
    ).strip().upper()

    DEMO_MOVEMENT_B_TO_A: str = os.getenv(
        "WAREHOUSE18_RFID_DEMO_MOVEMENT_B_TO_A",
        "GR",
    ).strip().upper()