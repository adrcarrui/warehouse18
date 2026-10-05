"""Envío piloto de una única entrada validada del outbox a mySim Tests.

Por defecto solo realiza una simulación local. El POST exige simultáneamente
--send-once y WAREHOUSE_SYNC_ALLOW_HTTP_POST=SEND_ONE_MYSIM_TESTS.
No contiene bucle, no selecciona otra entrada y no reintenta peticiones HTTP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests


for parent in Path(__file__).resolve().parents:
    if (parent / "src" / "warehouse18").is_dir():
        sys.path.insert(0, str(parent / "src"))
        break

from warehouse18.infrastructure.integrations.mySim.config import MySimConfig
from warehouse_sync_outbox_runtime import (
    claim_ready_by_id,
    complete_error,
    complete_sent,
    default_worker_id,
    ensure_runtime_schema,
    get_mysim_target_system,
)


POST_UNLOCK_ENV = "WAREHOUSE_SYNC_ALLOW_HTTP_POST"
POST_UNLOCK_VALUE = "SEND_ONE_MYSIM_TESTS"
PILOT_TARGET = "mysim_tests"
PILOT_HOST = "tests.simeng.es"
MYSIM_TIMEZONE = ZoneInfo("Europe/Madrid")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PilotSendError(RuntimeError):
    def __init__(self, message: str, *, delivery_uncertain: bool):
        super().__init__(message)
        self.delivery_uncertain = delivery_uncertain


def positive_id(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return int(value) > 0 and str(value).strip() not in {"", "0"}
    except (TypeError, ValueError):
        return False


def optional_id(value: Any) -> int | None:
    if isinstance(value, dict):
        value = value.get("id")
    if value in (None, "", 0, "0"):
        return None
    if not positive_id(value):
        raise ValueError(f"ID relacionado inválido: {value!r}")
    return int(value)


def canonical_payload_sha256(payload: dict[str, Any]) -> str:
    """Recalcula la misma huella de negocio usada durante la conciliación."""
    if payload.get("entity") != "Parts":
        raise ValueError("El payload no pertenece a Parts")
    for field in ("idCol", "movementType"):
        if not positive_id(payload.get(field)):
            raise ValueError(f"{field} inválido")
    quantity = Decimal(str(payload.get("quantity")))
    if not quantity.is_finite() or quantity <= 0:
        raise ValueError("Cantidad inválida")
    raw_date = str(payload.get("date") or "").strip()
    if raw_date.endswith("Z"):
        raw_date = raw_date[:-1] + "+00:00"
    stamp = datetime.fromisoformat(raw_date)
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        stamp = stamp.replace(tzinfo=MYSIM_TIMEZONE)
    stamp = stamp.astimezone(MYSIM_TIMEZONE)
    canonical = {
        "entity": "Parts",
        "idCol": int(payload["idCol"]),
        "movementType": int(payload["movementType"]),
        "date": stamp.strftime("%Y-%m-%d %H:%M:%S"),
        "quantity": format(quantity.normalize(), "f"),
        "sourceLocation": optional_id(payload.get("sourceLocation")),
        "destinationLocation": optional_id(payload.get("destinationLocation")),
        "doneBy": optional_id(payload.get("doneBy")),
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_entry(outbox_id: int, target_system: str) -> dict[str, Any] | None:
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        try:
            ensure_runtime_schema(db)
            row = db.execute(text("""
                SELECT id AS outbox_id, entity_id AS movement_id,
                       direction, target_system, entity_type, action,
                       status, retries, next_retry_at, sync_decision,
                       sync_reason, payload_json, payload_sha256,
                       remote_id, sent_at,
                       (next_retry_at IS NULL OR next_retry_at <= now()) AS retry_due
                FROM public.integration_outbox
                WHERE id = :outbox_id
                  AND target_system = :target_system
            """), {
                "outbox_id": outbox_id,
                "target_system": target_system,
            }).mappings().first()
            return dict(row) if row else None
        finally:
            db.rollback()


def validate_base_url(cfg: MySimConfig) -> str:
    parsed = urlparse(cfg.base_url)
    if parsed.scheme.lower() != "https" or (parsed.hostname or "").lower() != PILOT_HOST:
        raise ValueError(
            f"El piloto solo admite https://{PILOT_HOST}; base URL recibida: "
            f"{parsed.scheme}://{parsed.hostname or '<sin-host>'}"
        )
    if parsed.query or parsed.fragment or not parsed.path.rstrip("/").endswith("/api/v1/pub"):
        raise ValueError("MYSIM_BASE_URL debe terminar en /api/v1/pub y no llevar query ni fragmento")
    return cfg.base_url.rstrip("/") + "/set"


def validate_entry(
    row: dict[str, Any] | None,
    *,
    expected_outbox_id: int,
    expected_movement_id: int,
    expected_sha256: str,
) -> dict[str, Any]:
    if row is None:
        raise ValueError("No existe la entrada indicada para mysim_tests")
    expected = {
        "outbox_id": expected_outbox_id,
        "movement_id": expected_movement_id,
        "direction": "outbound",
        "target_system": PILOT_TARGET,
        "entity_type": "movement",
        "action": "sync",
        "sync_decision": "READY_TO_SYNC",
    }
    for field, value in expected.items():
        if row.get(field) != value:
            raise ValueError(f"{field} cambió: esperado={value!r}, actual={row.get(field)!r}")
    if row.get("status") not in {"pending", "error"}:
        raise ValueError(f"Estado no reclamable: {row.get('status')!r}")
    if not row.get("retry_due"):
        raise ValueError(f"La entrada todavía espera hasta {row.get('next_retry_at')}")
    if row.get("remote_id") is not None or row.get("sent_at") is not None:
        raise ValueError("La entrada ya tiene indicios de envío remoto")
    stored_sha256 = str(row.get("payload_sha256") or "").lower()
    if stored_sha256 != expected_sha256:
        raise ValueError("La huella guardada no coincide con la confirmada por el operador")
    payload = row.get("payload_json")
    if not isinstance(payload, dict) or not payload:
        raise ValueError("payload_json está vacío o no es un objeto JSON")
    actual_sha256 = canonical_payload_sha256(payload)
    if actual_sha256 != expected_sha256:
        raise ValueError("El contenido de payload_json no coincide con su huella guardada")
    if payload.get("id") not in (0, "0", None):
        raise ValueError("El payload no representa la creación de un movimiento nuevo")
    if int(payload.get("movementType", 0)) not in {57, 58, 59}:
        raise ValueError("Tipo de movimiento no permitido")
    if not positive_id(payload.get("doneBy")):
        raise ValueError("doneBy no es válido")
    if not positive_id(payload.get("destinationLocation")):
        raise ValueError("destinationLocation no es válido")
    marker = f"W18 movement_id={expected_movement_id}"
    if marker not in str(payload.get("movementDescription") or ""):
        raise ValueError("Falta el marcador único del movimiento en movementDescription")
    return payload


def parse_json_response(response: requests.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError as exc:
        raise PilotSendError(
            f"mySim devolvió una respuesta no JSON (HTTP {response.status_code})",
            delivery_uncertain=response.status_code < 300,
        ) from exc
    if not isinstance(body, dict):
        raise PilotSendError("mySim devolvió un JSON inesperado", delivery_uncertain=True)
    return body


def response_status(body: dict[str, Any]) -> int | None:
    value = body.get("status")
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def nested_value(value: Any, *path: str) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def extract_remote_id(body: dict[str, Any]) -> str | None:
    for path in (
        ("data", "data", "lastObject", "id"),
        ("data", "lastObject", "id"),
        ("lastObject", "id"),
    ):
        value = nested_value(body, *path)
        if positive_id(value):
            return str(int(value))
    return None


def validate_response(response: requests.Response) -> tuple[str, dict[str, Any]]:
    if response.is_redirect or response.is_permanent_redirect:
        raise PilotSendError(
            f"mySim redirigió la petición (HTTP {response.status_code})",
            delivery_uncertain=False,
        )
    body = parse_json_response(response)
    app_status = response_status(body)
    if response.status_code >= 400:
        uncertain = response.status_code == 408 or response.status_code >= 500
        raise PilotSendError(f"HTTP {response.status_code} devuelto por mySim", delivery_uncertain=uncertain)
    if app_status is None:
        raise PilotSendError("La respuesta no contiene un status válido", delivery_uncertain=True)
    if app_status >= 400:
        uncertain = app_status == 408 or app_status >= 500
        raise PilotSendError(f"mySim devolvió status {app_status}", delivery_uncertain=uncertain)
    if not 200 <= response.status_code < 300 or not 200 <= app_status < 300:
        raise PilotSendError("Respuesta de mySim no reconocida", delivery_uncertain=True)
    remote_id = extract_remote_id(body)
    if remote_id is None:
        raise PilotSendError(
            "mySim indicó éxito, pero no devolvió data.data.lastObject.id",
            delivery_uncertain=True,
        )
    return remote_id, body


def print_preview(
    *,
    row: dict[str, Any],
    payload: dict[str, Any],
    endpoint: str,
) -> None:
    print("ENVÍO PILOTO PREPARADO; todavía no se ha realizado ningún POST.")
    print(f"Target: {row['target_system']}")
    print(f"Outbox: {row['outbox_id']} | movimiento: {row['movement_id']}")
    print(f"Estado: {row['status']} | decisión: {row['sync_decision']} | reintentos: {row['retries']}")
    print(f"POST {endpoint}?entity=movement")
    print("Cabecera X-AUTH-TOKEN: configurada (valor oculto)")
    print("Body:")
    print(json.dumps([payload], ensure_ascii=False, indent=2, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simular o enviar una única entrada validada a mySim Tests."
    )
    parser.add_argument("--outbox-id", type=int, required=True)
    parser.add_argument("--expected-movement-id", type=int, required=True)
    parser.add_argument("--expected-payload-sha256", required=True)
    parser.add_argument(
        "--send-once",
        action="store_true",
        help="Realizar exactamente un POST; sin esta opción solo muestra la simulación.",
    )
    args = parser.parse_args()

    expected_sha256 = args.expected_payload_sha256.strip().lower()
    if not SHA256_RE.fullmatch(expected_sha256):
        parser.error("--expected-payload-sha256 debe contener 64 caracteres hexadecimales")

    try:
        target_system = get_mysim_target_system()
        if target_system != PILOT_TARGET:
            raise ValueError(f"El piloto exige MYSIM_TARGET_SYSTEM={PILOT_TARGET}")
        cfg = MySimConfig.from_env()
        endpoint = validate_base_url(cfg)
        row = load_entry(args.outbox_id, target_system)
        payload = validate_entry(
            row,
            expected_outbox_id=args.outbox_id,
            expected_movement_id=args.expected_movement_id,
            expected_sha256=expected_sha256,
        )
        print_preview(row=row, payload=payload, endpoint=endpoint)
    except Exception as exc:
        print(f"ERROR DE PREVALIDACIÓN: {exc}", file=sys.stderr)
        return 2

    if not args.send_once:
        print("MODO SIMULACIÓN: no se reclamó la entrada y no se llamó a mySim.")
        return 0
    if os.getenv(POST_UNLOCK_ENV) != POST_UNLOCK_VALUE:
        print(
            "ERROR: POST bloqueado. Además de --send-once debe definirse "
            f"{POST_UNLOCK_ENV}={POST_UNLOCK_VALUE}.",
            file=sys.stderr,
        )
        return 2

    worker_id = default_worker_id()
    try:
        claim = claim_ready_by_id(
            outbox_id=args.outbox_id,
            expected_movement_id=args.expected_movement_id,
            expected_payload_sha256=expected_sha256,
            worker_id=worker_id,
            target_system=target_system,
        )
    except Exception as exc:
        print(f"ERROR AL RECLAMAR: {exc}", file=sys.stderr)
        return 2
    if claim is None:
        print("ERROR: la entrada cambió después de la prevalidación y no fue reclamada.", file=sys.stderr)
        return 2

    try:
        if canonical_payload_sha256(claim.payload_json) != expected_sha256:
            raise PilotSendError("El payload cambió al reclamar la entrada", delivery_uncertain=False)
        print(f"ENVIANDO una sola entrada: outbox={claim.outbox_id} movimiento={claim.movement_id}")
        response = requests.post(
            endpoint,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
                "X-AUTH-TOKEN": cfg.token,
            },
            params={"entity": "movement"},
            json=[claim.payload_json],
            timeout=cfg.timeout,
            allow_redirects=False,
        )
        remote_id, response_body = validate_response(response)
        complete_sent(
            claim,
            remote_id=remote_id,
            response=response_body,
            reconciled=False,
        )
        print(f"ENVIADO Y CONFIRMADO: outbox={claim.outbox_id} | mySim movement id={remote_id}")
        return 0
    except requests.ConnectTimeout as exc:
        error = PilotSendError(f"ConnectTimeout: {exc}", delivery_uncertain=False)
    except (requests.ReadTimeout, requests.ConnectionError) as exc:
        error = PilotSendError(type(exc).__name__, delivery_uncertain=True)
    except PilotSendError as exc:
        error = exc
    except Exception as exc:
        error = PilotSendError(f"{type(exc).__name__}: {exc}", delivery_uncertain=True)

    try:
        complete_error(
            claim,
            error=str(error),
            delivery_uncertain=error.delivery_uncertain,
        )
    except Exception as state_exc:
        print(
            "ERROR CRÍTICO: no se pudo registrar el resultado del intento. "
            f"No repitas el POST; concilia primero. Detalle: {state_exc}",
            file=sys.stderr,
        )
        return 3
    if error.delivery_uncertain:
        print(
            f"RESULTADO INCIERTO: {error}. La entrada quedó bloqueada para conciliación; no repetir.",
            file=sys.stderr,
        )
    else:
        print(f"ENVÍO RECHAZADO SIN CONFIRMACIÓN: {error}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
