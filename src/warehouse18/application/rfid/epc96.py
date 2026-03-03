from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EPCSchema:
    magic: int
    version: int
    checksum: str
    families: dict[str, int]
    families_rev: dict[int, str]


def xor8(data: bytes) -> int:
    c = 0
    for b in data:
        c ^= b
    return c


def load_epc_schema(path: str | Path) -> EPCSchema:
    p = Path(path)
    raw: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))

    magic_hex = str(raw["magic_hex"]).strip().upper()
    if len(magic_hex) != 4:
        raise ValueError("magic_hex must be 2 bytes (4 hex chars), e.g. '17C0'")
    magic = int(magic_hex, 16)

    version = int(raw.get("version", 1))
    checksum = str(raw.get("checksum", "xor8"))

    families_raw: dict[str, Any] = raw.get("families", {})
    families: dict[str, int] = {k.strip().upper(): int(v) for k, v in families_raw.items()}

    # sanity checks
    for name, code in families.items():
        if not (0 <= code <= 255):
            raise ValueError(f"family code out of range 0..255: {name}={code}")

    rev: dict[int, str] = {}
    for name, code in families.items():
        if code in rev:
            raise ValueError(f"duplicate family code {code}: {rev[code]} and {name}")
        rev[code] = name

    return EPCSchema(magic=magic, version=version, checksum=checksum, families=families, families_rev=rev)


@dataclass(frozen=True)
class EPCParsed:
    epc: str
    magic: int
    version: int
    family_code: int
    family_name: str | None
    serial: int
    checksum_ok: bool


def parse_epc96(epc_hex: str, schema: EPCSchema) -> EPCParsed:
    epc_hex = epc_hex.strip().upper()
    if len(epc_hex) != 24:
        raise ValueError("EPC must be 96-bit (24 hex chars)")

    b = bytes.fromhex(epc_hex)
    magic = int.from_bytes(b[0:2], "big")
    version = b[2]
    fam = b[3]
    serial = int.from_bytes(b[4:11], "big")
    chk = b[11]

    if schema.checksum != "xor8":
        raise ValueError(f"Unsupported checksum algo: {schema.checksum}")

    ok = (xor8(b[0:11]) == chk)

    return EPCParsed(
        epc=epc_hex,
        magic=magic,
        version=version,
        family_code=fam,
        family_name=schema.families_rev.get(fam),
        serial=serial,
        checksum_ok=ok,
    )


def is_whitelisted(epc_hex: str, schema: EPCSchema) -> bool:
    try:
        p = parse_epc96(epc_hex, schema)
    except Exception:
        return False
    return (
        p.magic == schema.magic
        and p.version == schema.version
        and p.checksum_ok
        and (p.family_name is not None)
    )