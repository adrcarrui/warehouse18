from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReaderConfig:
    reader_id: str
    name: str
    host: str
    tcp_port: int
    enabled: bool = True


@dataclass(frozen=True)
class RouteConfig:
    reader_id: str
    antenna: int
    door_id: str
    zone_id: str
    zone_role: str
    logical_name: str
    location_id: int
    mysim_location_env: str | None = None
    enabled: bool = True


@dataclass(frozen=True)
class AntennaTopology:
    readers: dict[str, ReaderConfig]
    routes: dict[tuple[str, int], RouteConfig]

    def routes_for_reader(self, reader_id: str) -> list[RouteConfig]:
        return [
            route
            for route in self.routes.values()
            if route.reader_id == reader_id and route.enabled
        ]


def _parse_int(v: Any, field: str) -> int:
    if isinstance(v, int):
        return v
    raise ValueError(f"{field} must be int")


def _parse_str(v: Any, field: str) -> str:
    if not isinstance(v, str):
        raise ValueError(f"{field} must be str")
    value = v.strip()
    if not value:
        raise ValueError(f"{field} cannot be empty")
    return value


def _load_v2(raw: dict[str, Any]) -> AntennaTopology:
    readers_raw = raw.get("readers") or []
    doors_raw = raw.get("doors") or []

    if not readers_raw:
        raise ValueError("antenna_map.json: missing readers[]")
    if not doors_raw:
        raise ValueError("antenna_map.json: missing doors[]")

    readers: dict[str, ReaderConfig] = {}
    for r in readers_raw:
        reader_id = _parse_str(r.get("reader_id"), "reader_id")
        readers[reader_id] = ReaderConfig(
            reader_id=reader_id,
            name=str(r.get("name") or reader_id).strip(),
            host=_parse_str(r.get("host"), "host"),
            tcp_port=_parse_int(r.get("tcp_port"), "tcp_port"),
            enabled=bool(r.get("enabled", True)),
        )

    routes: dict[tuple[str, int], RouteConfig] = {}
    for door in doors_raw:
        door_id = _parse_str(door.get("door_id"), "door_id")
        reader_id = _parse_str(door.get("reader_id"), "reader_id")

        if reader_id not in readers:
            raise ValueError(
                f"antenna_map.json: door {door_id} references unknown reader_id={reader_id}"
            )

        zones = door.get("zones") or []
        if not zones:
            raise ValueError(f"antenna_map.json: door {door_id} has no zones[]")

        for z in zones:
            antenna = _parse_int(z.get("antenna"), "antenna")
            key = (reader_id, antenna)
            if key in routes:
                raise ValueError(
                    f"antenna_map.json: duplicate mapping for reader_id={reader_id} antenna={antenna}"
                )

            routes[key] = RouteConfig(
                reader_id=reader_id,
                antenna=antenna,
                door_id=door_id,
                zone_id=_parse_str(z.get("zone_id"), "zone_id").upper(),
                zone_role=_parse_str(z.get("zone_role"), "zone_role").upper(),
                logical_name=str(z.get("logical_name") or f"{door_id}:{antenna}").strip(),
                location_id=_parse_int(z.get("location_id"), "location_id"),
                mysim_location_env=(
                    str(z.get("mysim_location_env")).strip()
                    if z.get("mysim_location_env")
                    else None
                ),
                enabled=bool(z.get("enabled", True)),
            )

    return AntennaTopology(readers=readers, routes=routes)


def _load_legacy_v1(raw: dict[str, Any]) -> AntennaTopology:
    readers_raw = raw.get("readers") or []
    if not readers_raw:
        raise ValueError("antenna_map.json: missing readers[]")

    r0 = readers_raw[0]
    reader_id = str(r0.get("reader_id") or r0.get("name") or "reader-1").strip()

    readers = {
        reader_id: ReaderConfig(
            reader_id=reader_id,
            name=str(r0.get("name") or reader_id).strip(),
            host=str(r0.get("ip") or "127.0.0.1").strip(),
            tcp_port=int(r0.get("tcp_port") or 4001),
            enabled=True,
        )
    }

    routes: dict[tuple[str, int], RouteConfig] = {}
    for p in r0.get("ports") or []:
        antenna = _parse_int(p.get("port"), "port")
        location_id = p.get("location_id")
        enabled = bool(p.get("is_active", True))

        if location_id is None:
            continue

        routes[(reader_id, antenna)] = RouteConfig(
            reader_id=reader_id,
            antenna=antenna,
            door_id="legacy-door",
            zone_id=f"PORT_{antenna}",
            zone_role=str(p.get("direction") or "BOTH").upper(),
            logical_name=str(p.get("logical_name") or f"PORT_{antenna}").strip(),
            location_id=_parse_int(location_id, "location_id"),
            mysim_location_env=None,
            enabled=enabled,
        )

    return AntennaTopology(readers=readers, routes=routes)


def load_antenna_topology(path: str) -> AntennaTopology:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    version = int(raw.get("version") or 1)

    if version >= 2:
        return _load_v2(raw)

    return _load_legacy_v1(raw)


def resolve_antenna_map_path() -> str:
    p = os.getenv("WAREHOUSE18_ANTENNA_MAP")
    if p:
        return p
    return os.path.join(os.getcwd(), "config", "antenna_map.json")