from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from warehouse18.infrastructure.db import SessionLocal
from warehouse18.infrastructure.integrations.mySim.client import MySimClient, rows_normalized
from warehouse18.infrastructure.integrations.mySim.config import MySimConfig

router = APIRouter(prefix="/integrations", tags=["integrations"])


def check_db() -> dict[str, Any]:
    start = time.perf_counter()
    db = None

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        latency_ms = int((time.perf_counter() - start) * 1000)

        return {
            "ok": True,
            "latency_ms": latency_ms,
        }

    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "error": str(e),
        }

    finally:
        if db is not None:
            db.close()


def check_mysim() -> dict[str, Any]:
    start = time.perf_counter()

    try:
        cfg = MySimConfig.from_env()
        client = MySimClient(cfg)

        # Llamada ligera, no destructiva
        # Pedimos una sola cuenta para validar token, conectividad y parseo básico
        resp = client.get(entity="accounts", limit=1)
        rows = rows_normalized(resp)

        latency_ms = int((time.perf_counter() - start) * 1000)

        return {
            "ok": True,
            "latency_ms": latency_ms,
            "rows": len(rows),
        }

    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "ok": False,
            "latency_ms": latency_ms,
            "error": str(e),
        }


@router.get("/health")
def integrations_health() -> dict[str, Any]:
    db_status = check_db()
    mysim_status = check_mysim()

    if db_status["ok"] and mysim_status["ok"]:
        status = "ok"
    elif db_status["ok"] or mysim_status["ok"]:
        status = "degraded"
    else:
        status = "down"

    return {
        "status": status,
        "backend": {"ok": True},
        "database": db_status,
        "mysim": mysim_status,
    }