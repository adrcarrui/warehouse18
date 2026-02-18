from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AntennaPort:
    port: int
    logical_name: str
    location_id: int
    direction: str = "BOTH"
    is_active: bool = True
    notes: str = ""


@dataclass(frozen=True)
class AntennaMap:
    # key: port number -> AntennaPort
    ports: dict[int, AntennaPort]
    reader_name: str = "default"


def _parse_int(v: Any, field: str) -> int:
    if isinstance(v, int):
        return v
    raise ValueError(f"{field} must be int")


def load_antenna_map(path: str) -> AntennaMap:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    readers = raw.get("readers") or []
    if not readers:
        raise ValueError("antenna_map.json: missing readers[]")

    # MVP: usamos el primer reader. Si luego tienes varios lectores, lo ampliamos.
    r0 = readers[0]
    reader_name = str(r0.get("name") or "Reader")

    ports_raw = r0.get("ports") or []
    ports: dict[int, AntennaPort] = {}

    for p in ports_raw:
        port = _parse_int(p.get("port"), "port")
        is_active = bool(p.get("is_active", True))
        location_id = p.get("location_id")

        # Si no está activo o no tiene location_id, no se usa para movimientos
        if not is_active or location_id is None:
            continue

        ports[port] = AntennaPort(
            port=port,
            logical_name=str(p.get("logical_name") or f"PORT_{port}"),
            location_id=_parse_int(location_id, "location_id"),
            direction=str(p.get("direction") or "BOTH"),
            notes=str(p.get("notes") or ""),
            is_active=is_active,
        )

    return AntennaMap(ports=ports, reader_name=reader_name)


def resolve_antenna_map_path() -> str:
    """
    Prioridad:
    1) ENV WAREHOUSE18_ANTENNA_MAP
    2) ./config/antenna_map.json (cwd)
    """
    p = os.getenv("WAREHOUSE18_ANTENNA_MAP")
    if p:
        return p

    return os.path.join(os.getcwd(), "config", "antenna_map.json")
