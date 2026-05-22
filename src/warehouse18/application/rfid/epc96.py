from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EPC96_HEX_LEN = 24
EPC96_BYTE_LEN = 12
OBJECT_ID_BYTE_LEN = 3
TID_SERIAL_BYTE_LEN = 6
MAX_OBJECT_ID = (1 << (OBJECT_ID_BYTE_LEN * 8)) - 1
ZERO_TID_SERIAL_HEX = "0" * (TID_SERIAL_BYTE_LEN * 2)


@dataclass(frozen=True)
class EPCSchema:
    magic: int
    checksum: str
    families: dict[str, int]
    families_rev: dict[int, str]
    display_padding: dict[str, int]
    format: str = "warehouse18-epc96-v1"
    object_id_bytes: int = OBJECT_ID_BYTE_LEN
    tid_serial_bytes: int = TID_SERIAL_BYTE_LEN


@dataclass(frozen=True)
class EPCParsed:
    epc: str
    magic: int
    family_code: int
    family_name: str | None
    object_id: int
    tid_serial_hex: str
    checksum_ok: bool
    tracking_mode: str

    @property
    def serial(self) -> int:
        # Alias para no romper código viejo que usa parsed.serial.
        return self.object_id

    @property
    def version(self) -> None:
        # El nuevo estándar ya no lleva versión.
        return None


def normalize_hex(value: str) -> str:
    return str(value).strip().replace(" ", "").upper()


def xor8(data: bytes) -> int:
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum


def load_epc_schema(path: str | Path) -> EPCSchema:
    p = Path(path)
    raw: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))

    magic_hex = normalize_hex(str(raw["magic_hex"]))
    if len(magic_hex) != 2:
        raise ValueError("magic_hex must be 1 byte, e.g. '18'")

    magic = int(magic_hex, 16)

    if not (0 <= magic <= 0xFF):
        raise ValueError(f"magic out of range 0..255: {magic}")

    checksum = str(raw.get("checksum", "xor8")).strip().lower()

    families_raw: dict[str, Any] = raw.get("families", {})
    families: dict[str, int] = {
        name.strip().upper(): int(code)
        for name, code in families_raw.items()
    }

    for name, code in families.items():
        if not (0 <= code <= 255):
            raise ValueError(f"family code out of range 0..255: {name}={code}")

    families_rev: dict[int, str] = {}

    for name, code in families.items():
        if code in families_rev:
            raise ValueError(
                f"duplicate family code {code}: {families_rev[code]} and {name}"
            )
        families_rev[code] = name

    display_padding_raw: dict[str, Any] = raw.get("display_padding", {})
    display_padding: dict[str, int] = {
        name.strip().upper(): int(value)
        for name, value in display_padding_raw.items()
    }

    object_id_bytes = int(raw.get("object_id_bytes", OBJECT_ID_BYTE_LEN))
    tid_serial_bytes = int(raw.get("tid_serial_bytes", TID_SERIAL_BYTE_LEN))

    if object_id_bytes != OBJECT_ID_BYTE_LEN:
        raise ValueError("Warehouse18 EPC96 v1 expects object_id_bytes=3")

    if tid_serial_bytes != TID_SERIAL_BYTE_LEN:
        raise ValueError("Warehouse18 EPC96 v1 expects tid_serial_bytes=6")

    return EPCSchema(
        magic=magic,
        checksum=checksum,
        families=families,
        families_rev=families_rev,
        display_padding=display_padding,
        format=str(raw.get("format", "warehouse18-epc96-v1")),
        object_id_bytes=object_id_bytes,
        tid_serial_bytes=tid_serial_bytes,
    )


def parse_epc96(epc_hex: str, schema: EPCSchema) -> EPCParsed:
    epc_hex = normalize_hex(epc_hex)

    if len(epc_hex) != EPC96_HEX_LEN:
        raise ValueError("EPC must be 96-bit, 24 hex chars")

    try:
        data = bytes.fromhex(epc_hex)
    except ValueError as exc:
        raise ValueError("EPC must be valid hexadecimal") from exc

    if len(data) != EPC96_BYTE_LEN:
        raise ValueError("EPC must be 12 bytes")

    if schema.checksum != "xor8":
        raise ValueError(f"Unsupported checksum algo: {schema.checksum}")

    magic = data[0]
    family_code = data[1]
    object_id = int.from_bytes(data[2:5], byteorder="big")
    tid_serial_hex = data[5:11].hex().upper()
    tracking_mode = (
        "bulk"
        if tid_serial_hex == ZERO_TID_SERIAL_HEX
        else "serialized"
    )
    received_checksum = data[11]
    checksum_ok = xor8(data[:11]) == received_checksum

    return EPCParsed(
        epc=epc_hex,
        magic=magic,
        family_code=family_code,
        family_name=schema.families_rev.get(family_code),
        object_id=object_id,
        tid_serial_hex=tid_serial_hex,
        checksum_ok=checksum_ok,
        tracking_mode=tracking_mode,
    )


def is_whitelisted(epc_hex: str, schema: EPCSchema) -> bool:
    try:
        parsed = parse_epc96(epc_hex, schema)
    except Exception:
        return False

    return (
        parsed.magic == schema.magic
        and parsed.checksum_ok
        and parsed.family_name is not None
    )


def extract_tid_serial(tid_hex: str) -> bytes:
    tid_hex = normalize_hex(tid_hex)

    try:
        tid = bytes.fromhex(tid_hex)
    except ValueError as exc:
        raise ValueError("TID must be valid hexadecimal") from exc

    if len(tid) < TID_SERIAL_BYTE_LEN:
        raise ValueError("TID too short")

    return tid[-TID_SERIAL_BYTE_LEN:]


def build_epc96(
    *,
    family_name: str,
    object_id: int,
    tid_hex: str,
    schema: EPCSchema,
) -> str:
    family_name = family_name.strip().upper()

    if family_name not in schema.families:
        raise ValueError(f"Unsupported family/class: {family_name}")

    if not (0 <= object_id <= MAX_OBJECT_ID):
        raise ValueError(f"object_id must fit in 3 bytes: 0..{MAX_OBJECT_ID}")

    payload = bytes([schema.magic])
    payload += bytes([schema.families[family_name]])
    payload += object_id.to_bytes(OBJECT_ID_BYTE_LEN, byteorder="big")
    payload += extract_tid_serial(tid_hex)

    checksum = xor8(payload)

    return (payload + bytes([checksum])).hex().upper()


def format_item_key(parsed: EPCParsed, schema: EPCSchema) -> str | None:
    if parsed.family_name is None:
        return None

    padding = schema.display_padding.get(parsed.family_name, 6)
    return f"{parsed.family_name}-{parsed.object_id:0{padding}d}"