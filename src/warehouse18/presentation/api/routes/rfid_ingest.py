from __future__ import annotations
from dataclasses import dataclass
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from warehouse18.rfid_settings import RfidSettings
from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import StockContainer, Movement, MovementType
from warehouse18.presentation.api.schemas import RfidIngestIn
from warehouse18.presentation.api.routes.rfid_events import publish_rfid_event

router = APIRouter(prefix="/rfid", tags=["rfid"])
logger = logging.getLogger("warehouse18.rfid")

ITC_MARKER = bytes.fromhex(os.getenv("WAREHOUSE18_RFID_ITC_MARKER", "17C0"))
TYPE_USER = int(os.getenv("WAREHOUSE18_RFID_TYPE_USER", "01"), 16)
TYPE_ITEM = int(os.getenv("WAREHOUSE18_RFID_TYPE_ITEM", "02"), 16)

USER_BIND_TTL_SECONDS = int(
    os.getenv("WAREHOUSE18_RFID_USER_BIND_TTL_SECONDS", "20")
)

DEMO_DOOR_ID = os.getenv(
    "WAREHOUSE18_RFID_DEMO_DOOR_ID",
    "door_demo_1",
)

CROSS_WINDOW_SECONDS = int(
    os.getenv("WAREHOUSE18_RFID_CROSS_WINDOW_SECONDS", "3")
)

COOLDOWN_SECONDS = int(
    os.getenv("WAREHOUSE18_RFID_COOLDOWN_SECONDS", "6")
)

COOLDOWN_SECONDS = int(os.getenv("WAREHOUSE18_RFID_MOVE_COOLDOWN_SECONDS", "3"))

# cooldown por transición: (stock_container_id, from_location_id, to_location_id) -> last_ts
_last_move_ts: dict[tuple[int, int | None, int], datetime] = {}

# GC simple para evitar crecimiento infinito
_LAST_MOVE_GC_EVERY_S = float(os.getenv("WAREHOUSE18_RFID_MOVE_GC_EVERY_S", "5.0"))
_LAST_MOVE_TTL_S = float(os.getenv("WAREHOUSE18_RFID_MOVE_TTL_S", "60.0"))
_last_move_gc_ts: float = 0.0

_mt_cache: dict[str, int] = {}  # movement_type_code -> movement_type_id
# cooldown para lecturas de badge de usuario
USER_SEEN_COOLDOWN_SECONDS = int(
    os.getenv("WAREHOUSE18_RFID_USER_SEEN_COOLDOWN_SECONDS", "2")
)

_last_user_seen: dict[tuple[int, str | None], datetime] = {}
@dataclass(frozen=True)
class UserBadgeParsed:
    epc: str
    user_id: int

def xor8(data: bytes) -> int:
    x = 0
    for b in data:
        x ^= b
    return x

def zone_for_antenna(ant: int) -> str | None:
    if ant == RfidSettings.ZONE_DOOR_ANT:
        return "DOOR"
    if ant == RfidSettings.ZONE_AISLE1_ANT:
        return "AISLE_1"
    if ant == RfidSettings.ZONE_AISLE2_ANT:
        return "AISLE_2"
    return None

def parse_user_badge(epc_hex: str) -> Optional[UserBadgeParsed]:
    h = epc_hex.strip().upper().replace(" ", "")
    if h.startswith("0X"):
        h = h[2:]
    if len(h) != 24:
        return None
    try:
        b = bytes.fromhex(h)
        logger.info(
            "DBG USER BYTES | b0_2=%s b2=%s b11=%s xor=%s",
            b[0:2].hex(),
            b[2],
            b[11],
            xor8(b[0:11]),
        )
    except ValueError:
        return None

    if b[0:2] != RfidSettings.ITC_MARKER:
        return None
    if b[2] != RfidSettings.TYPE_USER:
        return None
    if b[11] != xor8(b[0:11]):
        return None

    user_id = int.from_bytes(b[4:11], "big")
    return UserBadgeParsed(epc=h, user_id=user_id)

def _rfid_state(request: Request) -> dict:
    st = getattr(request.app.state, "rfid_state", None)
    if not isinstance(st, dict):
        request.app.state.rfid_state = {"presence": {}, "last_user_by_zone": {}}
        st = request.app.state.rfid_state
    st.setdefault("presence", {})
    st.setdefault("last_user_by_zone", {})
    return st

def update_presence(request: Request, user_id: int, now: datetime) -> None:
    _rfid_state(request)["presence"][int(user_id)] = now

def bind_user_to_zone(request: Request, zone: str, user_id: int, now: datetime) -> None:
    _rfid_state(request)["last_user_by_zone"][zone] = {"user_id": int(user_id), "ts": now}

def get_bound_user_for_zone(request: Request, zone: str, now: datetime) -> int | None:
    """
    Devuelve el user_id bindeado a esa zona si no ha expirado el TTL.
    """
    st = _rfid_state(request)
    entry = st["last_user_by_zone"].get(zone)
    if not entry:
        return None

    ts = entry.get("ts")
    user_id = entry.get("user_id")
    if ts is None or user_id is None:
        return None

    # TTL
    age = (now - ts).total_seconds()
    if age > RfidSettings.USER_BIND_TTL_SECONDS:
        return None

    return int(user_id)

def normalize_epc(v: str) -> str:
    return v.strip().upper()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_mt_id(db: Session, code: str) -> int:
    mt_id = _mt_cache.get(code)
    if mt_id:
        return mt_id

    mt = db.query(MovementType).filter(MovementType.code == code).first()
    if not mt:
        raise HTTPException(
            status_code=409,
            detail=f"MovementType code '{code}' not found. Seed it first.",
        )
    _mt_cache[code] = mt.id
    return mt.id


async def _safe_publish_event(payload: dict[str, Any]) -> None:
    try:
        await publish_rfid_event(payload)
    except Exception:
        # El monitor no debe tumbar el ingest
        return


@router.post("/ingest")
async def ingest_rfid_event(
    body: RfidIngestIn,
    request: Request,
    db: Session = Depends(get_db),
):
    epc = normalize_epc(body.epc)
    now = _utcnow()

    logger.info("RFID INGEST RECEIVED | epc=%s antenna=%s rssi=%s", epc, body.antenna, body.rssi)

    async def _emit_and_return(status: str, reason: str, extra: dict[str, Any] | None = None):
        payload: dict[str, Any] = {
            "type": "tag",
            "ts": now.isoformat(),
            "epc": epc,
            "antenna": body.antenna,
            "rssi": body.rssi,
            "status": status,
            "reason": reason,
        }
        if extra:
            payload.update(extra)

        await _safe_publish_event(payload)

        resp = {"status": status, "reason": reason, "epc": epc, "antenna": body.antenna}
        if extra:
            resp.update(extra)
        return resp

    # --------------------------------------------------
    # USER BADGE DETECTION
    # --------------------------------------------------
    logger.info(
        "DBG USER PARSE INPUT | epc=%s len=%s marker=%s type_user=%s",
        epc,
        len(epc),
        RfidSettings.ITC_MARKER.hex(),
        RfidSettings.TYPE_USER,
    )
    parsed_user = parse_user_badge(epc)
    if parsed_user is not None:

        if body.rssi is not None and body.rssi < RfidSettings.USER_MIN_RSSI:
            return await _emit_and_return(
                "ignored",
                "user_rssi_too_low",
                {
                    "user_id": parsed_user.user_id,
                    "min_rssi": RfidSettings.USER_MIN_RSSI,
                },
            )

        zone = zone_for_antenna(body.antenna)
        key = (parsed_user.user_id, zone)

        last = _last_user_seen.get(key)
        if last:
            diff = (now - last).total_seconds()

            if diff < USER_SEEN_COOLDOWN_SECONDS:
                return await _emit_and_return(
                    "ignored",
                    "user_cooldown",
                    {
                        "user_id": parsed_user.user_id,
                        "zone": zone,
                        "seconds_since_last": diff,
                        "cooldown_seconds": USER_SEEN_COOLDOWN_SECONDS,
                    },
                )

        _last_user_seen[key] = now
        update_presence(request, parsed_user.user_id, now)

        if zone is not None:
            bind_user_to_zone(request, zone, parsed_user.user_id, now)

        logger.info(
            "RFID USER SEEN | user_id=%s zone=%s antenna=%s rssi=%s",
            parsed_user.user_id,
            zone,
            body.antenna,
            body.rssi,
        )

        return await _emit_and_return(
            "ok",
            "user_seen",
            {
                "user_id": parsed_user.user_id,
                "zone": zone,
                "door_id": RfidSettings.DEMO_DOOR_ID,
                "presence_ttl_seconds": RfidSettings.USER_PRESENCE_TTL_SECONDS,
                "bind_ttl_seconds": RfidSettings.USER_BIND_TTL_SECONDS if zone else None,
            },
        )

    # --------------------------------------------------
    # ANTENNA MAP
    # --------------------------------------------------

    antenna_map = getattr(request.app.state, "antenna_map", None)
    if antenna_map is None:
        logger.warning("RFID INGEST | antenna_map NOT loaded")
        return await _emit_and_return("ignored", "antenna_map_not_loaded")

    port = antenna_map.ports.get(body.antenna)
    if not port:
        logger.warning("RFID INGEST | antenna_not_mapped | antenna=%s", body.antenna)
        return await _emit_and_return("ignored", "antenna_not_mapped", {"antenna": body.antenna})

    to_location_id = port.location_id
    base_extra = {"logical_name": port.logical_name, "to_location_id": to_location_id}

    zone = zone_for_antenna(body.antenna)
    bound_user_id = get_bound_user_for_zone(request, zone, now) if zone else None

    create_movements = True
    if not create_movements:
        return await _emit_and_return("ok", "movements_disabled", base_extra)

    # --------------------------------------------------
    # FIND CONTAINER
    # --------------------------------------------------

    sc = (
        db.query(StockContainer)
        .filter(StockContainer.container_code == epc, StockContainer.is_active.is_(True))
        .first()
    )

    if not sc:
        logger.info("RFID INGEST | container_not_found | epc=%s", epc)
        return await _emit_and_return("ignored", "container_not_found", base_extra)

    from_location_id = sc.location_id

    if from_location_id == to_location_id:
        return await _emit_and_return(
            "ok",
            "no_change",
            {
                **base_extra,
                "stock_container_id": sc.id,
                "from_location_id": from_location_id,
            },
        )

    # --------------------------------------------------
    # COOLDOWN GC
    # --------------------------------------------------

    global _last_move_gc_ts
    t = time.time()

    if (t - _last_move_gc_ts) > _LAST_MOVE_GC_EVERY_S and _last_move_ts:
        _last_move_gc_ts = t
        cutoff = datetime.fromtimestamp(t - _LAST_MOVE_TTL_S, tz=timezone.utc)
        dead = [k for k, ts in _last_move_ts.items() if ts < cutoff]

        for k in dead:
            _last_move_ts.pop(k, None)

    key = (sc.id, from_location_id, int(to_location_id))

    last = _last_move_ts.get(key)
    if last:
        diff = (now - last).total_seconds()

        if diff < COOLDOWN_SECONDS:
            return await _emit_and_return(
                "ignored",
                "cooldown",
                {
                    **base_extra,
                    "stock_container_id": sc.id,
                    "from_location_id": from_location_id,
                    "to_location_id": to_location_id,
                    "seconds_since_last": diff,
                    "cooldown_seconds": COOLDOWN_SECONDS,
                },
            )

    # --------------------------------------------------
    # CREATE MOVEMENT
    # --------------------------------------------------

    mt_id = _get_mt_id(db, "GT")

    try:

        mv = Movement(
            movement_type_id=mt_id,
            item_id=sc.item_id,
            quantity=sc.quantity,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            reference_type="container",
            reference_id=sc.id,
            user_id=bound_user_id,
            notes=(
            f"RFID ingest ant={body.antenna} rssi={body.rssi} ({port.logical_name}) "
            f"zone={zone} user_id={bound_user_id}"
            ),
        )

        db.add(mv)

        sc.location_id = to_location_id

        db.commit()
        db.refresh(mv)

        _last_move_ts[(sc.id, from_location_id, int(to_location_id))] = now

        return await _emit_and_return(
            "ok",
            "movement_created",
            {
                **base_extra,
                "movement_id": mv.id,
                "stock_container_id": sc.id,
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
                "zone": zone,
                "user_id": bound_user_id,
            },
        )

    except IntegrityError as e:
        db.rollback()

        return await _emit_and_return(
            "ignored",
            "db_integrity_error",
            {**base_extra, "detail": str(e.orig)},
        )
    
@router.post("/ingest/batch")
async def ingest_rfid_batch(
    body: dict[str, list[RfidIngestIn]],
    request: Request,
    db: Session = Depends(get_db),
):
    reads = body.get("reads", [])
    out: list[dict[str, Any]] = []

    # Importa tu función actual (si está en el mismo módulo, llama directo)
    for r in reads:
        # reutiliza la lógica existente: llama a ingest_rfid_event(r, request, db)
        # pero ojo: ingest_rfid_event hace commit/rollback por lectura.
        # Para empezar, lo dejamos simple:
        res = await ingest_rfid_event(r, request, db)  # type: ignore
        out.append(res)

    return {"count": len(out), "results": out}