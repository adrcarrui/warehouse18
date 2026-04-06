from warehouse18.config import settings
import logging
import os
print(os.getenv("WAREHOUSE18_RFID_LOG_LEVEL"))
log_level = os.getenv("WAREHOUSE18_RFID_LOG_LEVEL", "INFO").upper()
print("##LOG LEVEL: ", log_level)
logging.basicConfig(
    level=getattr(logging, getattr(settings, "rfid_log_level", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
import asyncio

from warehouse18.presentation.api.routes.rfid_events import publish_rfid_event
from warehouse18.application.rfid.service import RFIDReaderService, RFIDServiceConfig
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from warehouse18.rfid_settings import RfidSettings
from warehouse18.infrastructure.db import get_db
from warehouse18.presentation.api.schemas import (
    ReceiveContainerIn, ConsumeContainerIn, TransferContainerIn,
    ReceiveAssetIn, TransferAssetIn, IssueAssetIn,
    OkOut
)

from warehouse18.infrastructure.config.antenna_map import (
    load_antenna_topology,
    resolve_antenna_map_path,
)

from warehouse18.presentation.api.routes.users import router as users_router
from warehouse18.presentation.api.routes.locations import router as locations_router
from warehouse18.presentation.api.routes.items import router as items_router
from warehouse18.presentation.api.routes.assets import router as assets_router
from warehouse18.presentation.api.routes.stock_containers import router as stock_containers_router
from warehouse18.presentation.api.routes.inventory_stock import router as inventory_stock_router
from warehouse18.presentation.api.routes.movement_types import router as movement_types_router
from warehouse18.presentation.api.routes.movements import router as movements_router
from warehouse18.presentation.api.routes.rfid_events import router as rfid_events_router
from warehouse18.presentation.api.routes.rfid_ingest import router as rfid_ingest_router
from warehouse18.presentation.api.routes.settings import router as settings_router
from warehouse18.presentation.api.routes.rfid_schema import router as rfid_schema_router
from warehouse18.presentation.api.routes.integrations_health import router as integrations_health_router
from warehouse18.application.settings_service import SettingsService
from warehouse18.presentation.api.routes.mysim_item_location import router as mysim_item_location_router



app = FastAPI(
    title="Warehouse18 API",
    root_path=settings.root_path,
    docs_url=f"{settings.api_prefix}/docs",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    debug=settings.debug,
    
)

app.state.rfid_state = {
    "presence": {},           # user_id -> datetime (última vez visto)
    "last_user_by_zone": {},  # zone -> {"user_id": int, "ts": datetime}
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size", "X-Total-Pages", "Link"],
)

app.include_router(users_router, prefix=settings.api_prefix)
app.include_router(locations_router, prefix=settings.api_prefix)
app.include_router(items_router, prefix=settings.api_prefix)
app.include_router(assets_router, prefix=settings.api_prefix)
app.include_router(stock_containers_router, prefix=settings.api_prefix)
app.include_router(inventory_stock_router, prefix=settings.api_prefix)
app.include_router(movement_types_router, prefix=settings.api_prefix)
app.include_router(movements_router, prefix=settings.api_prefix)
app.include_router(rfid_events_router, prefix=settings.api_prefix)
app.include_router(rfid_ingest_router, prefix=settings.api_prefix)
app.include_router(settings_router, prefix=settings.api_prefix)
app.include_router(rfid_schema_router, prefix=settings.api_prefix)
app.include_router(integrations_health_router, prefix=settings.api_prefix)
app.include_router(mysim_item_location_router, prefix=settings.api_prefix)

app.state.settings_service = SettingsService(ttl_seconds=2)

@app.on_event("startup")
def _load_antenna_map_on_startup():
    path = resolve_antenna_map_path()
    topology = load_antenna_topology(path)
    app.state.antenna_topology = topology

    print(
        f"[antenna_map] loaded readers={list(topology.readers.keys())} "
        f"routes={sorted(topology.routes.keys())} from {path}"
    )

@app.on_event("startup")
async def _start_rfid_reader_on_startup():
    print("DBG | env WAREHOUSE18_RFID_INTERNAL_ENABLE =", os.getenv("WAREHOUSE18_RFID_INTERNAL_ENABLE"))
    print("DBG | settings.rfid_internal_enable =", getattr(settings, "rfid_internal_enable", None))
    print("DBG | settings class =", type(settings))

    enable = bool(getattr(settings, "rfid_internal_enable", False))
    if not enable:
        logging.getLogger("warehouse18.rfid.service").info(
            "RFID internal reader disabled (WAREHOUSE18_RFID_INTERNAL_ENABLE=0)"
        )
        return

    topology = getattr(app.state, "antenna_topology", None)
    if topology is None:
        raise RuntimeError("antenna_topology not loaded on startup")

    if getattr(app.state, "rfid_services", None):
        return

    app.state.rfid_services = {}

    for reader_id, reader in topology.readers.items():
        if not reader.enabled:
            continue

        ants = sorted(
            {
                route.antenna
                for route in topology.routes_for_reader(reader_id)
                if route.enabled
            }
        )

        if not ants:
            logging.getLogger("warehouse18.rfid.service").warning(
                "Skipping RFID reader %s because it has no active routes", reader_id
            )
            continue

        cfg = RFIDServiceConfig(
            reader_id=reader.reader_id,
            host=reader.host,
            port=reader.tcp_port,
            ants=ants,
        )

        svc = RFIDReaderService(
            cfg,
            publish=publish_rfid_event,
            loop=asyncio.get_running_loop(),
        )
        svc.start()
        app.state.rfid_services[reader_id] = svc

        logging.getLogger("warehouse18.rfid.service").info(
            "RFID internal reader started | reader_id=%s host=%s port=%s ants=%s",
            reader.reader_id,
            reader.host,
            reader.tcp_port,
            ants,
        )


@app.on_event("shutdown")
def _stop_rfid_reader_on_shutdown():
    services = getattr(app.state, "rfid_services", {}) or {}
    for reader_id, svc in services.items():
        try:
            svc.stop()
        except Exception:
            logging.getLogger("warehouse18.rfid.service").exception(
                "Failed stopping RFID reader %s", reader_id
            )

@app.get(f"{settings.api_prefix}/health")
def health():
    return {"ok": True}


def _map_db_error(e: Exception) -> HTTPException:
    # Si viene de SQLAlchemy envuelto como DBAPIError, saca el "orig"
    orig = e.orig if isinstance(e, DBAPIError) and hasattr(e, "orig") else e

    # SQLSTATE (Postgres): psycopg3 suele exponer .sqlstate, psycopg2 suele exponer .pgcode
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)

    # Check / FK / Unique => 409
    if sqlstate in ("23514", "23503", "23505"):
        return HTTPException(status_code=409, detail=str(orig))

    # Muchos RAISE EXCEPTION tuyos caen aquí:
    low = str(orig).lower()
    if any(s in low for s in ["not found", "cannot", "not enough", "invalid", "already"]):
        return HTTPException(status_code=409, detail=str(orig))

    return HTTPException(status_code=500, detail="Internal error")


# -------------------------
# Containers (consumibles)
# -------------------------

@app.post(f"{settings.api_prefix}/scan/container/receive", response_model=OkOut)
def receive_container_api(body: ReceiveContainerIn, db: Session = Depends(get_db)):
    sql = text("SELECT receive_container(:container_code,:item_id,:location_code,:qty,:user_id,:notes);")
    try:
        movement_id = db.execute(sql, {
            "container_code": body.container_code,
            "item_id": body.item_id,
            "location_code": body.location_code,
            "qty": body.qty,
            "user_id": body.user_id,
            "notes": body.notes,
        }).scalar_one()
        db.commit()
        return OkOut(movement_id=movement_id)
    except Exception as e:
        db.rollback()
        raise _map_db_error(e)


@app.post(f"{settings.api_prefix}/scan/container/consume", response_model=OkOut)
def consume_container_api(body: ConsumeContainerIn, db: Session = Depends(get_db)):
    sql = text("SELECT consume_from_container(:container_code,:qty,:user_id,:notes);")
    try:
        movement_id = db.execute(sql, {
            "container_code": body.container_code,
            "qty": body.qty,
            "user_id": body.user_id,
            "notes": body.notes,
        }).scalar_one()
        db.commit()
        return OkOut(movement_id=movement_id)
    except Exception as e:
        db.rollback()
        raise _map_db_error(e)


@app.post(f"{settings.api_prefix}/scan/container/transfer", response_model=OkOut)
def transfer_container_api(body: TransferContainerIn, db: Session = Depends(get_db)):
    sql = text("SELECT transfer_container(:container_code,:to_location_code,:user_id,:notes);")
    try:
        movement_id = db.execute(sql, {
            "container_code": body.container_code,
            "to_location_code": body.to_location_code,
            "user_id": body.user_id,
            "notes": body.notes,
        }).scalar_one()
        db.commit()
        return OkOut(movement_id=movement_id)
    except Exception as e:
        db.rollback()
        raise _map_db_error(e)


# -------------------------
# Assets (serializados)
# -------------------------

@app.post(f"{settings.api_prefix}/scan/asset/receive", response_model=OkOut)
def receive_asset_api(body: ReceiveAssetIn, db: Session = Depends(get_db)):
    sql = text("SELECT receive_asset(:asset_code,:item_id,:to_location_code,:user_id,:notes,:create_enrichment);")
    try:
        movement_id = db.execute(sql, {
            "asset_code": body.asset_code,
            "item_id": body.item_id,
            "to_location_code": body.to_location_code,
            "user_id": body.user_id,
            "notes": body.notes,
            "create_enrichment": body.create_enrichment,
        }).scalar_one()
        db.commit()
        return OkOut(movement_id=movement_id)
    except Exception as e:
        db.rollback()
        raise _map_db_error(e)


@app.post(f"{settings.api_prefix}/scan/asset/transfer", response_model=OkOut)
def transfer_asset_api(body: TransferAssetIn, db: Session = Depends(get_db)):
    sql = text("SELECT move_asset_to_location(:asset_code,:to_location_code,:user_id,:notes);")
    try:
        movement_id = db.execute(sql, {
            "asset_code": body.asset_code,
            "to_location_code": body.to_location_code,
            "user_id": body.user_id,
            "notes": body.notes,
        }).scalar_one()
        db.commit()
        return OkOut(movement_id=movement_id)
    except Exception as e:
        db.rollback()
        raise _map_db_error(e)


@app.post(f"{settings.api_prefix}/scan/asset/issue", response_model=OkOut)
def issue_asset_api(body: IssueAssetIn, db: Session = Depends(get_db)):
    sql = text("SELECT issue_asset(:asset_code,:user_id,:notes,:new_status);")
    try:
        movement_id = db.execute(sql, {
            "asset_code": body.asset_code,
            "user_id": body.user_id,
            "notes": body.notes,
            "new_status": body.new_status,
        }).scalar_one()
        db.commit()
        return OkOut(movement_id=movement_id)
    except Exception as e:
        db.rollback()
        raise _map_db_error(e)
