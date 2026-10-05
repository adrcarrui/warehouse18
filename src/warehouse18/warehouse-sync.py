"""Consulta artículo, movimientos mySim y outbox; valida, concilia y decide.
Hasta tres intentos por consulta mySim; modo local de solo lectura por defecto.
Nunca envía movimientos. Las decisiones y alertas solo se guardan con el
doble desbloqueo --apply-db-actions + WAREHOUSE_SYNC_ALLOW_DB_WRITES.
Pausas de 2 y 4 segundos ante timeout, conexión o status 408/500/502/503/504.

Guardar en scripts/ y ejecutar desde la raíz del proyecto:
    python scripts/warehouse-sync-check-item.py --part-code "GEN-010838"
Usa MYSIM_BASE_URL, MYSIM_TOKEN y MYSIM_TARGET_SYSTEM de la configuración.
Códigos de salida: 0 encontrado, 1 sin coincidencias, 2 error.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

# Permite ejecutarlo sin instalar el paquete warehouse18.
for parent in Path(__file__).resolve().parents:
    if (parent / "src" / "warehouse18").is_dir():
        sys.path.insert(0, str(parent / "src"))
        break
from warehouse18.infrastructure.integrations.mySim.config import MySimConfig


class LookupError(RuntimeError):
    pass


class TransientLookupError(LookupError):
    pass


TRANSIENT_STATUSES = {408, 500, 502, 503, 504}
MYSIM_MOVEMENT_TYPES = {
    "GR": (57, "Good Receipt"),
    "GI": (58, "Good Issue"),
    "GT": (59, "Good Transfer"),
}
MYSIM_TIMEZONE = ZoneInfo("Europe/Madrid")
MYSIM_HISTORY_LIMIT = 1000
EXACT_DATE_TOLERANCE_SECONDS = 1
POSSIBLE_DATE_TOLERANCE_SECONDS = 300
DB_WRITE_CONFIRMATION_ENV = "WAREHOUSE_SYNC_ALLOW_DB_WRITES"
DB_WRITE_CONFIRMATION_VALUE = "APPLY_SYNC_STATE"
SUPPORTED_MYSIM_TARGETS = frozenset({"mysim_tests", "mysim_itc"})


def get_mysim_target_system() -> str:
    """Obtiene el entorno mySim y falla si no está definido explícitamente."""
    load_dotenv()
    target_system = os.getenv("MYSIM_TARGET_SYSTEM", "").strip().lower()
    if not target_system:
        raise ValueError(
            "Falta MYSIM_TARGET_SYSTEM; debe ser mysim_tests o mysim_itc"
        )
    if target_system not in SUPPORTED_MYSIM_TARGETS:
        raise ValueError(
            f"MYSIM_TARGET_SYSTEM no válido: {target_system!r}; "
            "debe ser mysim_tests o mysim_itc"
        )
    return target_system


def parse_rows(response: requests.Response) -> list[dict[str, Any]]:
    # Un 404 puede indicar un endpoint o entidad incorrectos. Es un error,
    # no una confirmación de que el artículo no existe.
    if response.status_code in TRANSIENT_STATUSES:
        raise TransientLookupError(f"HTTP {response.status_code}")
    if not 200 <= response.status_code < 300:
        raise LookupError(f"Respuesta HTTP {response.status_code}; existencia no determinada.")
    try:
        body = response.json()
    except ValueError as exc:
        raise LookupError("mySim no devolvió JSON; existencia no determinada.") from exc
    if not isinstance(body, dict):
        raise LookupError("Formato de respuesta inesperado.")
    try:
        status = int(body["status"])
    except (KeyError, ValueError, TypeError) as exc:
        raise LookupError("Respuesta sin un status válido.") from exc
    if status in TRANSIENT_STATUSES:
        raise TransientLookupError(f"mySim status {status}")
    if status != 200:
        raise LookupError(f"mySim devolvió status {status}; existencia no determinada.")
    data = body.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise LookupError("Se esperaba data.data como lista; existencia no determinada.")
    rows = data["data"]
    if any(not isinstance(row, dict) for row in rows):
        raise LookupError("La respuesta contiene registros inválidos.")
    return rows


def query_with_retries(cfg: MySimConfig, params: dict) -> list[dict[str, Any]]:
    # Tres intentos totales, sin reintentos internos del adaptador HTTP.
    for attempt in range(1, 4):
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")
        print(f"{stamp} | intento={attempt}/3 | consultando...", flush=True)
        started = time.perf_counter()
        http = "-"
        try:
            with requests.Session() as session:
                response = session.get(
                    f"{cfg.base_url.rstrip('/')}/get",
                    params=params,
                    headers={"X-AUTH-TOKEN": cfg.token, "Accept": "application/json"},
                    timeout=cfg.timeout,
                    allow_redirects=False,
                )
            http = str(response.status_code)
            rows = parse_rows(response)
        except requests.exceptions.SSLError:
            print(f"  {time.perf_counter() - started:.3f}s | ERROR TLS; sin reintento", flush=True)
            raise LookupError("Error de certificado/TLS; existencia no determinada.") from None
        except (requests.Timeout, requests.ConnectionError, TransientLookupError) as exc:
            reason = str(exc) if isinstance(exc, TransientLookupError) else type(exc).__name__
            print(f"  {time.perf_counter() - started:.3f}s | HTTP={http} | {reason}", flush=True)
            if attempt == 3:
                raise LookupError("Tres intentos fallidos; existencia no determinada. Sincronización pendiente de comprobar.") from None
            delay = 2 ** attempt
            print(f"  Reintento en {delay}s", flush=True)
            time.sleep(delay)
            continue
        except (LookupError, requests.RequestException) as exc:
            print(f"  {time.perf_counter() - started:.3f}s | HTTP={http} | ERROR; sin reintento", flush=True)
            if isinstance(exc, LookupError):
                raise
            raise LookupError(f"{type(exc).__name__}; existencia no determinada.") from None
        print(f"  {time.perf_counter() - started:.3f}s | HTTP={http} | consulta válida | registros={len(rows)}", flush=True)
        return rows
    raise AssertionError("Bucle de consulta agotado")


def find_item(cfg: MySimConfig, part_code: str) -> dict[str, Any] | None:
    if not part_code.strip():
        raise LookupError("El código del artículo no puede estar vacío.")
    # Conservar guiones, barras y otros caracteres del código original.
    safe_code = part_code.replace("\\", "\\\\").replace("'", "''")
    query = f"t.partId = '{safe_code}'"
    params = {
        "entity": "parts",
        "extraQuery": base64.b64encode(query.encode("utf-8")).decode("ascii"),
        "limit": "2",  # Dos registros bastan para detectar una ambigüedad.
    }
    print(f"Artículo: {part_code} | timeout={cfg.timeout}", flush=True)
    rows = query_with_retries(cfg, params)
    if not rows:
        return None
    if len(rows) > 1:
        raise LookupError("Hay varias coincidencias para el código. Revisar antes de sincronizar.")
    item = rows[0]
    if item.get("partId") != part_code:
        raise LookupError("El código devuelto no coincide exactamente con el solicitado.")
    item_id = item.get("id")
    if isinstance(item_id, bool) or not str(item_id).isdigit() or int(item_id) <= 0:
        raise LookupError("El artículo no tiene un ID interno válido.")
    return item


def get_last_movement(cfg: MySimConfig, item_id: int) -> dict[str, Any] | None:
    """Último por fecha del movimiento; no por fecha de edición.

    Si hay movimientos con la misma fecha máxima, mySim puede devolver
    cualquiera de ellos: todavía no se aplica un desempate por ID.
    """
    query = f"t.idCol = '{int(item_id)}' AND t.entity = 'Parts'"
    params = {
        "entity": "movement",
        "extraQuery": base64.b64encode(query.encode("utf-8")).decode("ascii"),
        "orderBy": base64.b64encode(b"t.date").decode("ascii"),
        "orderType": "DESC",
        "limit": "1",
    }
    print(f"\nConsultando último movimiento de Parts id={item_id} (date DESC)", flush=True)
    rows = query_with_retries(cfg, params)
    if not rows:
        return None
    if len(rows) != 1:
        raise LookupError("mySim no respetó el límite de movimientos.")
    movement = rows[0]
    if str(movement.get("idCol")) != str(item_id) or movement.get("entity") != "Parts":
        raise LookupError("El movimiento devuelto no pertenece al artículo solicitado.")
    if not movement.get("date") or not movement.get("id"):
        raise LookupError("El movimiento devuelto no tiene fecha o ID válido.")
    return movement


def get_item_movements_for_reconciliation(
    cfg: MySimConfig,
    item_id: int,
    limit: int = MYSIM_HISTORY_LIMIT,
) -> list[dict[str, Any]]:
    """Carga una sola página ordenada para conciliar todos los pendientes."""
    query = f"t.idCol = '{int(item_id)}' AND t.entity = 'Parts'"
    params = {
        "entity": "movement",
        "extraQuery": base64.b64encode(query.encode("utf-8")).decode("ascii"),
        "orderBy": base64.b64encode(b"t.date").decode("ascii"),
        "orderType": "DESC",
        "limit": str(limit),
    }
    print(
        f"\nConciliación: consultando hasta {limit} movimientos mySim de Parts id={item_id}",
        flush=True,
    )
    return query_with_retries(cfg, params)


def list_pending_movements(
    part_code: str,
    target_system: str,
    include_blocked: bool = False,
) -> list[dict[str, Any]]:
    """Lee la cola del artículo sin reclamar trabajos ni cambiar estados.

    to_jsonb permite leer item_key incluso con el esquema antiguo adjunto,
    que todavía no contiene esa columna.
    """
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    statement = text("""
        SELECT o.id AS outbox_id, o.status AS outbox_status, o.retries,
               o.next_retry_at, o.created_at AS outbox_created_at,
               o.entity_id AS movement_id, o.target_system,
               m.created_at AS movement_date,
               m.item_id AS local_item_id,
               COALESCE(NULLIF(to_jsonb(m)->>'item_key', ''),
                        NULLIF(o.payload_json->>'item_key', ''), i.item_code) AS part_code,
               mt.code AS movement_type,
               m.quantity, m.from_location_id, m.to_location_id,
               m.user_id, m.notes,
               to_jsonb(src) AS source_location_data,
               to_jsonb(dst) AS destination_location_data,
               COALESCE((SELECT jsonb_agg(to_jsonb(r) ORDER BY r.id)
                         FROM public.location_external_refs r
                         WHERE r.location_id = m.from_location_id
                           AND lower(trim(r.source_system)) = :target_system), '[]'::jsonb) AS source_external_refs,
               COALESCE((SELECT jsonb_agg(to_jsonb(r) ORDER BY r.id)
                         FROM public.location_external_refs r
                         WHERE r.location_id = m.to_location_id
                           AND lower(trim(r.source_system)) = :target_system), '[]'::jsonb) AS destination_external_refs,
               to_jsonb(m) AS movement_data,
               o.payload_json,
               (m.id IS NOT NULL) AS movement_exists,
               (o.next_retry_at IS NULL OR o.next_retry_at <= now()) AS retry_due
        FROM public.integration_outbox AS o
        LEFT JOIN public.movements AS m ON m.id = o.entity_id
        LEFT JOIN public.items AS i ON i.id = m.item_id
        LEFT JOIN public.movement_types AS mt ON mt.id = m.movement_type_id
        LEFT JOIN public.locations AS src ON src.id = m.from_location_id
        LEFT JOIN public.locations AS dst ON dst.id = m.to_location_id
        WHERE o.direction = 'outbound'
          AND o.target_system = :target_system
          AND o.entity_type = 'movement'
          AND o.action = 'sync'
          AND o.status IN ('pending', 'error', 'processing', 'failed')
          AND (
              CAST(:include_blocked AS boolean)
              OR COALESCE(o.sync_decision, '') <> 'BLOCKED_VALIDATION'
          )
          AND COALESCE(o.sync_decision, '') <> 'DUPLICATE_CONFIRMED'
          AND COALESCE(NULLIF(to_jsonb(m)->>'item_key', ''),
                       NULLIF(o.payload_json->>'item_key', ''), i.item_code) = :part_code
        ORDER BY m.created_at ASC NULLS LAST, o.entity_id ASC, o.id ASC
    """)
    with SessionLocal() as db:
        try:
            db.execute(text("SET TRANSACTION READ ONLY"))
            rows = [
                dict(row)
                for row in db.execute(
                    statement,
                    {
                        "part_code": part_code,
                        "target_system": target_system,
                        "include_blocked": include_blocked,
                    },
                ).mappings()
            ]
        finally:
            db.rollback()
    with SessionLocal() as db:
        try:
            db.execute(text("SET TRANSACTION READ ONLY"))
            existing = db.execute(text("""
                SELECT id, code, status, movement_id, updated_at
                FROM public.alerts
                WHERE source = 'movement'
                  AND code IN (
                      'MYSIM_SYNC_VALIDATION_FAILED',
                      'MYSIM_SYNC_CHECK_UNAVAILABLE',
                      'MYSIM_SYNC_DUPLICATE'
                  )
                  AND movement_id = ANY(CAST(:movement_ids AS bigint[]))
                ORDER BY updated_at DESC NULLS LAST, id DESC
            """), {'movement_ids': [row['movement_id'] for row in rows]}).mappings().all() if rows else []
        finally:
            db.rollback()
    for row in rows:
        row['existing_sync_alerts'] = [dict(a) for a in existing if a['movement_id'] == row['movement_id']]
    return rows


def positive_id(value: Any) -> bool:
    return not isinstance(value, bool) and str(value).isdigit() and int(value) > 0


def movement_datetime(value: Any) -> datetime:
    """Normaliza la fecha local y conserva el instante original."""
    stamp = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("La fecha del movimiento no tiene zona horaria")
    return stamp.astimezone(MYSIM_TIMEZONE)


def build_mysim_payload(
    *,
    mysim_item_id: int,
    row: dict[str, Any],
    validation: dict[str, Any],
    references: dict[str, Any],
) -> dict[str, Any]:
    """Construye exactamente la previsualización; no realiza ningún envío."""
    if not validation.get("local_data_ok"):
        raise ValueError("El movimiento no supera la validación local")
    movement_code = row.get("movement_type")
    type_data = MYSIM_MOVEMENT_TYPES.get(movement_code)
    if type_data is None:
        raise ValueError("El tipo de movimiento no está soportado")
    if references.get("user", {}).get("status") != "VERIFICADO":
        raise ValueError("El usuario no está verificado en mySim")
    if references.get("destination", {}).get("status") != "VERIFICADO":
        raise ValueError("La localización de destino no está verificada en mySim")

    quantity = Decimal(str(row.get("quantity")))
    if not quantity.is_finite() or quantity <= 0 or quantity != quantity.to_integral_value():
        raise ValueError("La cantidad no puede representarse como entero sin modificarla")

    movement_id = int(row["movement_id"])
    marker = f"W18 movement_id={movement_id}"
    notes = str(row.get("notes") or "").strip()
    description = f"{marker} | {notes}" if notes else marker
    movement_type_id, movement_type_name = type_data
    payload: dict[str, Any] = {
        "id": 0,
        "entity": "Parts",
        "idCol": int(mysim_item_id),
        "movementType": movement_type_id,
        "movementType.name": movement_type_name,
        "quantity": int(quantity),
        "movementDescription": description,
        "date": movement_datetime(row["movement_date"]).strftime("%Y-%m-%d %H:%M:%S"),
        "doneBy": int(references["user"]["id"]),
        "parentRecord": row["part_code"],
    }
    if row.get("to_location_id") is not None:
        payload["destinationLocation"] = int(references["destination"]["id"])
    return payload


def build_request_preview(mysim_item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Describe la futura petición sin incluir URL, token ni efectuar I/O."""
    return {
        "method": "POST",
        "path": "/set",
        "params": {"entity": "movement"},
        "json": [payload],
    }


def mysim_datetime(value: Any) -> datetime:
    """Interpreta las fechas sin zona de mySim como Europe/Madrid."""
    if isinstance(value, datetime):
        stamp = value
    else:
        raw = str(value or "").strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        stamp = datetime.fromisoformat(raw)
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        stamp = stamp.replace(tzinfo=MYSIM_TIMEZONE)
    return stamp.astimezone(MYSIM_TIMEZONE)


def canonical_optional_id(value: Any) -> int | None:
    """Normaliza relaciones vacías de mySim; no acepta texto arbitrario."""
    if isinstance(value, dict):
        value = value.get("id")
    if value in (None, "", 0, "0"):
        return None
    if isinstance(value, bool) or not str(value).isdigit() or int(value) <= 0:
        raise ValueError(f"ID relacionado inválido: {value!r}")
    return int(value)


def canonical_quantity(value: Any) -> str:
    quantity = Decimal(str(value))
    if not quantity.is_finite() or quantity <= 0:
        raise ValueError("Cantidad inválida")
    return format(quantity.normalize(), "f")


def canonical_movement(value: dict[str, Any]) -> dict[str, Any]:
    """Campos de negocio usados para la huella y la conciliación."""
    entity = value.get("entity")
    if entity != "Parts":
        raise ValueError(f"Entidad no soportada: {entity!r}")
    if not positive_id(value.get("idCol")):
        raise ValueError("idCol inválido")
    if not positive_id(value.get("movementType")):
        raise ValueError("movementType inválido")
    stamp = mysim_datetime(value.get("date"))
    return {
        "entity": "Parts",
        "idCol": int(value["idCol"]),
        "movementType": int(value["movementType"]),
        "date": stamp.strftime("%Y-%m-%d %H:%M:%S"),
        "quantity": canonical_quantity(value.get("quantity")),
        "sourceLocation": canonical_optional_id(value.get("sourceLocation")),
        "destinationLocation": canonical_optional_id(value.get("destinationLocation")),
        # mySim contiene movimientos históricos con doneBy=0; se conservan
        # como ausencia para que produzcan una discrepancia, no se descarten.
        "doneBy": canonical_optional_id(value.get("doneBy")),
    }


def movement_fingerprint(value: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    canonical = canonical_movement(value)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), canonical


def compare_canonical_movements(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], float]:
    mismatches = {}
    for field in (
        "entity",
        "idCol",
        "movementType",
        "quantity",
        "destinationLocation",
        "doneBy",
    ):
        if expected[field] != actual[field]:
            mismatches[field] = {"expected": expected[field], "actual": actual[field]}
    date_delta = abs(
        (mysim_datetime(expected["date"]) - mysim_datetime(actual["date"])).total_seconds()
    )
    if date_delta > EXACT_DATE_TOLERANCE_SECONDS:
        mismatches["date"] = {
            "expected": expected["date"],
            "actual": actual["date"],
            "delta_seconds": date_delta,
        }
    return mismatches, date_delta


def movement_evidence(remote: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "mysim_id": remote.get("id"),
        "movementId": remote.get("movementId"),
        "date": remote.get("date"),
        "movementType": remote.get("movementType"),
        **extra,
    }


def reconcile_payload(
    payload: dict[str, Any],
    history: list[dict[str, Any]],
    *,
    history_limit: int = MYSIM_HISTORY_LIMIT,
) -> dict[str, Any]:
    """Clasifica sin decidir por el texto de movementDescription."""
    fingerprint, expected = movement_fingerprint(payload)
    description = str(payload.get("movementDescription") or "")
    marker = description.split(" | ", 1)[0] if description.startswith("W18 movement_id=") else None
    exact = []
    marker_conflicts = []
    possible = []
    valid_dates = []
    invalid_rows = 0

    for remote in history:
        remote_description = str(remote.get("movementDescription") or "")
        marker_match = bool(
            marker
            and (
                remote_description == marker
                or remote_description.startswith(marker + " | ")
            )
        )
        try:
            _, actual = movement_fingerprint(remote)
            valid_dates.append(mysim_datetime(actual["date"]))
        except (InvalidOperation, TypeError, ValueError):
            invalid_rows += 1
            if marker_match:
                marker_conflicts.append(
                    movement_evidence(remote, reason="Marcador coincidente en movimiento no comparable")
                )
            continue

        mismatches, date_delta = compare_canonical_movements(expected, actual)
        if not mismatches:
            exact.append(
                movement_evidence(
                    remote,
                    fingerprint=fingerprint,
                    marker_match=marker_match,
                )
            )
            continue
        if marker_match:
            marker_conflicts.append(movement_evidence(remote, mismatches=mismatches))
            continue
        if (
            actual["movementType"] == expected["movementType"]
            and actual["quantity"] == expected["quantity"]
            and date_delta <= POSSIBLE_DATE_TOLERANCE_SECONDS
        ):
            possible.append(movement_evidence(remote, mismatches=mismatches))

    common = {
        "payload_sha256": fingerprint,
        "canonical_payload": expected,
        "history_rows": len(history),
        "history_limit": history_limit,
        "invalid_history_rows": invalid_rows,
    }
    if marker_conflicts:
        return {
            "status": "POSIBLE_DUPLICADO",
            "reason": "El marcador aparece, pero los campos de negocio no coinciden",
            "matches": marker_conflicts,
            **common,
        }
    if len(exact) == 1:
        return {
            "status": "DUPLICADO_CONFIRMADO",
            "reason": "Coincidencia única de todos los campos de negocio",
            "matches": exact,
            **common,
        }
    if len(exact) > 1:
        return {
            "status": "POSIBLE_DUPLICADO",
            "reason": "Más de un movimiento mySim coincide con todos los campos",
            "matches": exact,
            **common,
        }
    if possible:
        return {
            "status": "POSIBLE_DUPLICADO",
            "reason": "Hay movimientos cercanos en fecha, tipo y cantidad",
            "matches": possible,
            **common,
        }

    history_truncated = len(history) >= history_limit
    if history_truncated:
        expected_date = mysim_datetime(expected["date"])
        if not valid_dates:
            return {
                "status": "NO_DETERMINADO",
                "reason": "El historial alcanzó el límite y no contiene fechas comparables",
                "matches": [],
                **common,
            }
        oldest_loaded = min(valid_dates)
        if expected_date < oldest_loaded - timedelta(seconds=EXACT_DATE_TOLERANCE_SECONDS):
            return {
                "status": "NO_DETERMINADO",
                "reason": "El movimiento es anterior a la página de historial recuperada",
                "oldest_loaded": oldest_loaded.isoformat(),
                "matches": [],
                **common,
            }
    return {
        "status": "NO_ENCONTRADO",
        "reason": "No hay coincidencias completas ni candidatos cercanos",
        "matches": [],
        **common,
    }


class MovementReconciler:
    """Carga el historial remoto una vez y reutiliza el resultado."""

    def __init__(self, cfg: MySimConfig, mysim_item_id: int):
        self.cfg = cfg
        self.mysim_item_id = mysim_item_id
        self.history: list[dict[str, Any]] | None = None
        self.error: str | None = None

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.history is None and self.error is None:
            try:
                self.history = get_item_movements_for_reconciliation(
                    self.cfg,
                    self.mysim_item_id,
                )
            except LookupError as exc:
                self.error = str(exc)
        fingerprint, canonical = movement_fingerprint(payload)
        if self.error is not None:
            return {
                "status": "NO_DETERMINADO",
                "reason": self.error,
                "payload_sha256": fingerprint,
                "canonical_payload": canonical,
                "matches": [],
            }
        return reconcile_payload(payload, self.history or [])

    def check_prior_state(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Compara el estado remoto anterior con el movimiento que se quiere aplicar."""
        if self.history is None and self.error is None:
            try:
                self.history = get_item_movements_for_reconciliation(
                    self.cfg,
                    self.mysim_item_id,
                )
            except LookupError as exc:
                self.error = str(exc)
        if self.error is not None:
            return {
                "status": "NO_DETERMINADO",
                "blocking": True,
                "reason": self.error,
            }
        return assess_prior_state(payload, self.history or [])


def assess_prior_state(
    payload: dict[str, Any],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    """El origen y el estado previo no intervienen durante esta etapa."""
    return {
        "status": "ORIGEN_NO_COMPROBADO",
        "blocking": False,
        "reason": "La comprobación del origen está desactivada en esta etapa",
    }


def unresolved_references(
    row: dict[str, Any],
    references: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    unresolved = []
    if references.get("user", {}).get("status") != "VERIFICADO":
        unresolved.append(("user", references.get("user", {})))
    for role, field in (("destination", "to_location_id"),):
        if row.get(field) is not None and references.get(role, {}).get("status") != "VERIFICADO":
            unresolved.append((role, references.get(role, {})))
    return unresolved


def decide_movement(
    *,
    row: dict[str, Any],
    validation: dict[str, Any],
    references: dict[str, Any],
    payload: dict[str, Any] | None,
    payload_error: str | None,
    reconciliation: dict[str, Any] | None,
    prior_state: dict[str, Any] | None,
    previous_blocker_id: int | None,
) -> dict[str, Any]:
    """Decisión pura: no consulta servicios ni modifica estados."""
    movement_id = int(row["movement_id"])
    if previous_blocker_id is not None:
        return {
            "status": "WAITING_FOR_PREVIOUS",
            "reason": f"El movimiento anterior {previous_blocker_id} todavía no está resuelto",
            "movement_id": movement_id,
            "previous_blocker_id": previous_blocker_id,
            "blocks_following": False,
        }
    if validation.get("issues"):
        return {
            "status": "BLOCKED_VALIDATION",
            "reason": "; ".join(validation["issues"]),
            "movement_id": movement_id,
            "blocks_following": True,
        }
    if validation.get("waits"):
        return {
            "status": "BLOCKED_VALIDATION",
            "reason": "; ".join(validation["waits"]),
            "movement_id": movement_id,
            "blocks_following": True,
        }
    unresolved = unresolved_references(row, references)
    if unresolved:
        unavailable = [
            f"{role}: {ref.get('status')}"
            for role, ref in unresolved
            if ref.get("status") == "NO_DETERMINADO"
        ]
        failures = [f"{role}: {ref.get('status')}" for role, ref in unresolved]
        return {
            "status": "CHECK_UNAVAILABLE" if unavailable else "BLOCKED_VALIDATION",
            "reason": "; ".join(unavailable or failures),
            "movement_id": movement_id,
            "blocks_following": True,
        }
    if payload is None:
        return {
            "status": "BLOCKED_VALIDATION",
            "reason": payload_error or "No se pudo construir el payload",
            "movement_id": movement_id,
            "blocks_following": True,
        }
    if prior_state is None:
        return {
            "status": "CHECK_UNAVAILABLE",
            "reason": "No se comprobó el estado anterior del artículo en mySim",
            "movement_id": movement_id,
            "blocks_following": True,
        }
    if prior_state.get("status") == "NO_DETERMINADO":
        return {
            "status": "CHECK_UNAVAILABLE",
            "reason": prior_state.get("reason") or "No se pudo determinar el estado anterior",
            "movement_id": movement_id,
            "blocks_following": True,
        }
    if prior_state.get("blocking"):
        return {
            "status": "BLOCKED_STATE_MISMATCH",
            "reason": prior_state.get("reason") or "El estado anterior no es compatible",
            "movement_id": movement_id,
            "blocks_following": True,
        }
    if reconciliation is None:
        return {
            "status": "CHECK_UNAVAILABLE",
            "reason": "No se completó la conciliación con mySim",
            "movement_id": movement_id,
            "blocks_following": True,
        }
    status = reconciliation.get("status")
    mapping = {
        "NO_ENCONTRADO": "READY_TO_SYNC",
        "DUPLICADO_CONFIRMADO": "DUPLICATE_CONFIRMED",
        "POSIBLE_DUPLICADO": "POSSIBLE_DUPLICATE",
        "NO_DETERMINADO": "CHECK_UNAVAILABLE",
    }
    decision_status = mapping.get(status, "CHECK_UNAVAILABLE")
    return {
        "status": decision_status,
        "reason": reconciliation.get("reason") or f"Estado de conciliación inesperado: {status}",
        "movement_id": movement_id,
        "payload_sha256": reconciliation.get("payload_sha256"),
        # Un duplicado confirmado ya está aplicado remotamente y no impide
        # evaluar el siguiente. Cualquier otro estado conserva el orden.
        "blocks_following": decision_status != "DUPLICATE_CONFIRMED",
    }


def validate_movement(row: dict[str, Any]) -> dict[str, Any]:
    """Validaciones locales. No presupone equivalencia de IDs con mySim."""
    issues = []
    pending = []
    waits = []
    data = row.get("movement_data") or {}
    if not row.get("movement_exists"):
        issues.append("El movimiento local no existe")
    if not row.get("part_code"):
        issues.append("Falta el código del artículo")
    if not row.get("movement_date"):
        issues.append("Falta la fecha del movimiento")
    else:
        try:
            stamp = row['movement_date']
            if not isinstance(stamp, datetime):
                stamp = datetime.fromisoformat(str(stamp))
            if stamp.tzinfo is None or stamp.utcoffset() is None:
                issues.append("Fecha sin zona horaria; falta definir la conversión a mySim")
        except (ValueError, TypeError):
            issues.append("Fecha de movimiento inválida")
    if data.get("review_status") != "confirmed":
        issues.append("La revisión del movimiento no está confirmada")
    if not positive_id(data.get("mysim_user_id")):
        issues.append("Falta un mysim_user_id válido para el autor; no se sustituye por el revisor")
    else:
        pending.append(f"Comprobar usuario {data['mysim_user_id']} en mySim")
    # IDs de tipos ya utilizados por el adaptador del proyecto.
    type_ids = {code: values[0] for code, values in MYSIM_MOVEMENT_TYPES.items()}
    movement_type = row.get("movement_type")
    if movement_type not in type_ids:
        issues.append(f"Tipo de movimiento sin correspondencia definida: {movement_type}")
    try:
        raw_quantity = row.get("quantity")
        if isinstance(raw_quantity, bool):
            raise ValueError()
        quantity = Decimal(str(raw_quantity))
        if not quantity.is_finite() or quantity <= 0:
            raise ValueError()
        if quantity != quantity.to_integral_value():
            issues.append("Cantidad fraccionaria: el envío permanece bloqueado para no redondearla")
    except (InvalidOperation, ValueError, TypeError):
        issues.append("Cantidad ausente o no positiva/finita")
    # Requisitos preliminares para GR/GI/GT; no generan un payload de envío.
    # En esta etapa el origen no se comprueba para ningún tipo.
    required = {"GR": {"destination"}, "GI": {"destination"}, "GT": {"destination"}}
    for side, id_field, data_field, label in (
        ("destination", "to_location_id", "destination_location_data", "destino"),
    ):
        location_id = row.get(id_field)
        if location_id is None:
            if side in required.get(movement_type, set()):
                issues.append(f"Falta ubicación de {label}")
            continue
        if not positive_id(location_id):
            issues.append(f"ID local de {label} inválido")
            continue
        location = row.get(data_field)
        if not isinstance(location, dict) or str(location.get('id')) != str(location_id):
            issues.append(f"La ubicación local de {label} {location_id} no existe")
        elif location.get('is_active') is False:
            issues.append(f"La ubicación local de {label} {location_id} está inactiva")
        pending.append(f"Resolver ubicación local de {label} {location_id} a ID mySim y comprobarla")
    if data.get('mysim_movement_id') or data.get('mysim_synced_at') or data.get('mysim_sync_status') in {'sent', 'synced'}:
        issues.append("Hay indicios de sincronización previa; conciliar para evitar duplicados")
    if row.get('outbox_status') == 'processing':
        waits.append("Entrada en procesamiento; revisar quién la tiene reclamada")
    if row.get('outbox_status') == 'failed':
        waits.append("Estado failed; falta definir su recuperación")
    if not row.get('retry_due', True):
        waits.append("Todavía no se ha cumplido next_retry_at")
    pending.append("Comprobar duplicados en el historial mySim; el último movimiento solo no basta")
    return {
        'issues': issues, 'pending': pending, 'waits': waits,
        'local_data_ok': not issues,
        'mysim_movement_type_id': type_ids.get(movement_type),
    }


class ReferenceResolver:
    """Consulta referencias una vez por ejecución. No persiste correspondencias."""
    def __init__(self, cfg: MySimConfig, target_system: str):
        self.cfg = cfg
        self.target_system = target_system
        self.cache = {}

    def lookup(self, entity: str, params: dict, expected_field: str, expected_value: Any) -> dict:
        key = (entity, expected_field, str(expected_value))
        if key in self.cache:
            return self.cache[key]
        try:
            rows = query_with_retries(self.cfg, {"entity": entity, "limit": "2", **params})
            if not rows:
                result = {'status': 'SIN_COINCIDENCIAS'}
            elif len(rows) != 1:
                result = {'status': 'AMBIGUO'}
            elif str(rows[0].get(expected_field)) != str(expected_value) or not positive_id(rows[0].get('id')):
                result = {'status': 'RESPUESTA_NO_COINCIDE'}
            elif rows[0].get('enabled') is False or str(rows[0].get('deleted', 0)) == '1':
                result = {'status': 'INACTIVO'}
            else:
                result = {'status': 'VERIFICADO', 'id': int(rows[0]['id']), 'row': rows[0]}
        except LookupError as exc:
            result = {'status': 'NO_DETERMINADO', 'detail': str(exc)}
        self.cache[key] = result
        return result

    def user(self, user_id: Any) -> dict:
        print(f"  Verificando autor mySim id={user_id}", flush=True)
        return self.lookup('accounts', {'id': str(user_id)}, 'id', user_id)

    def location(self, local: dict, refs: list) -> dict:
        metadata = {'local_id': local.get('id'), 'local_code': local.get('code')}
        ref, error = select_location_reference(
            local.get('id'), refs, self.target_system
        )
        if error:
            return {**metadata, 'status': error}
        external_id = str(ref.get('external_id') or '').strip()
        metadata.update(reference_id=ref.get('id'), external_id=external_id)
        if not positive_id(external_id):
            return {**metadata, 'status': 'EXTERNAL_ID_INVALIDO'}
        print(f"  Verificando ubicación local={local['id']} -> mySim id={external_id}", flush=True)
        result = self.lookup('location', {'id': str(int(external_id))}, 'id', int(external_id))
        expected_code = ref.get('external_code') or local.get('code')
        if result['status'] == 'VERIFICADO':
            actual_code = result['row'].get('locationCode')
            metadata.update(external_code=expected_code, actual_code=actual_code)
            if not expected_code:
                result = {**result, 'status': 'FALTA_CODIGO_PARA_CONTRASTAR'}
            elif actual_code != expected_code:
                result = {**result, 'status': 'CODIGO_NO_COINCIDE',
                          'detail': f"Código esperado={expected_code}; código mySim={actual_code}"}
        return {**result, **metadata}


def select_location_reference(
    local_id: Any,
    refs: list,
    target_system: str,
) -> tuple[dict | None, str | None]:
    # Una principal única tiene prioridad. Sin principal, debe haber un solo vínculo.
    candidates = [ref for ref in refs if isinstance(ref, dict)
                  and str(ref.get('location_id')) == str(local_id)
                  and str(ref.get('source_system', '')).strip().lower() == target_system]
    if not candidates:
        return None, 'SIN_VINCULO_MYSIM'
    primary = [ref for ref in candidates if ref.get('is_primary') is True]
    if len(primary) > 1:
        return None, 'VARIOS_VINCULOS_PRINCIPALES'
    if len(primary) == 1:
        return primary[0], None
    if len(candidates) == 1:
        return candidates[0], None
    return None, 'VARIOS_VINCULOS_SIN_PRINCIPAL'


def resolve_references(row: dict, resolver: ReferenceResolver) -> dict:
    references = {}
    data = row.get('movement_data') or {}
    user_id = data.get('mysim_user_id')
    if positive_id(user_id):
        references['user'] = resolver.user(user_id)
    else:
        references['user'] = {'status': 'FALTA_ID'}
    references['source'] = {
        'status': 'NO_COMPROBADO',
        'detail': 'La comprobación del origen está desactivada en esta etapa',
    }
    for side, field in [('destination', 'destination_location_data')]:
        location = row.get(field)
        if not isinstance(location, dict):
            references[side] = {'status': 'SIN_UBICACION_LOCAL'}
        else:
            references[side] = resolver.location(location, row.get(side + '_external_refs') or [])
    return references


def plan_sync_alerts(
    row: dict,
    validation: dict,
    references: dict,
    reconciliation: dict[str, Any] | None = None,
    prior_state: dict[str, Any] | None = None,
) -> list[dict]:
    """Devuelve acciones propuestas para alerts; nunca ejecuta escrituras.

    Solo se resuelven códigos propiedad de esta validación. No modifica
    MOVEMENT_WITHOUT_DONE_BY ni otras alertas del worker existente.
    """
    permanent = [{'kind': 'local_validation', 'message': issue} for issue in validation['issues']]
    unavailable = []
    duplicates = []
    state_mismatches = []
    for role, ref in references.items():
        if role == 'source':
            continue
        if role in {'source', 'destination'}:
            field = 'from_location_id' if role == 'source' else 'to_location_id'
            if row.get(field) is None:
                continue
        if ref['status'] == 'VERIFICADO':
            continue
        cause = {'kind': 'reference', 'role': role, 'status': ref['status'],
                 'local_id': ref.get('local_id'), 'external_id': ref.get('external_id'),
                 'message': ref.get('detail') or f"{role}: {ref['status']}"}
        (unavailable if ref['status'] == 'NO_DETERMINADO' else permanent).append(cause)
    if reconciliation:
        reconciliation_status = reconciliation['status']
        if reconciliation_status in {'DUPLICADO_CONFIRMADO', 'POSIBLE_DUPLICADO'}:
            duplicates.append({
                'kind': 'mysim_duplicate',
                'status': reconciliation_status,
                'payload_sha256': reconciliation.get('payload_sha256'),
                'mysim_ids': [match.get('mysim_id') for match in reconciliation.get('matches', [])],
                'message': f"{reconciliation_status}: {reconciliation['reason']}",
            })
        elif reconciliation_status == 'NO_DETERMINADO':
            unavailable.append({
                'kind': 'reconciliation',
                'status': reconciliation_status,
                'payload_sha256': reconciliation.get('payload_sha256'),
                'message': f"Conciliación mySim: {reconciliation['reason']}",
            })
    if prior_state and prior_state.get('status') in {
        'AVISO_ORIGEN_GI_DISTINTO', 'INCOHERENCIA_BLOQUEANTE'
    }:
        state_mismatches.append({
            'kind': 'prior_state',
            'status': prior_state['status'],
            'blocking': bool(prior_state.get('blocking')),
            'previous_destination': prior_state.get('previous_destination'),
            'expected_source': prior_state.get('expected_source'),
            'expected_destination': prior_state.get('expected_destination'),
            'message': prior_state['reason'],
        })
    validation_can_resolve = not permanent and not any(
        cause.get('kind') == 'reference' for cause in unavailable
    )
    unavailable_can_resolve = reconciliation is not None and not unavailable
    duplicate_can_resolve = bool(
        reconciliation and reconciliation.get('status') == 'NO_ENCONTRADO'
    )
    state_can_resolve = bool(prior_state and not prior_state.get('blocking'))
    definitions = [
        ('MYSIM_SYNC_VALIDATION_FAILED', 'mySim sync validation failed', permanent, validation_can_resolve),
        ('MYSIM_SYNC_CHECK_UNAVAILABLE', 'mySim sync checks unavailable', unavailable, unavailable_can_resolve),
        ('MYSIM_SYNC_DUPLICATE', 'Possible duplicate movement in mySim', duplicates, duplicate_can_resolve),
        ('MYSIM_SYNC_STATE_MISMATCH', 'mySim state differs before movement', state_mismatches, state_can_resolve),
    ]
    actions = []
    existing = row.get('existing_sync_alerts') or []
    for code, title, causes, can_resolve in definitions:
        same = [a for a in existing if a['code'] == code]
        active = [a for a in same if a['status'] in {'open', 'acknowledged'}]
        if len(active) > 1:
            actions.append({'action': 'REVISAR_ALERTAS_DUPLICADAS', 'code': code,
                            'existing_alert_ids': [a['id'] for a in active]})
            continue
        if not causes:
            if active:
                action = 'RESOLVER' if can_resolve else 'MANTENER_HASTA_COMPLETAR_COMPROBACIONES'
                actions.append({'action': action, 'code': code, 'existing_alert_id': active[0]['id']})
            continue
        action = 'ACTUALIZAR' if active else 'CREAR'
        alert = {
            'code': code, 'title': title,
            'message': f"Movement #{row['movement_id']}. Item: {row['part_code']}. " + '; '.join(c['message'] for c in causes),
            'severity': 'warning', 'status': active[0]['status'] if active else 'open',
            'source': 'movement', 'entity_type': 'movement', 'entity_id': str(row['movement_id']),
            'movement_id': row['movement_id'], 'item_id': row.get('local_item_id'),
            'epc': None,
            'metadata': {
                'operation': 'mysim_sync_validation', 'outbox_id': row['outbox_id'],
                'item_key': row['part_code'], 'causes': causes,
                'movement_code': row.get('movement_type'),
                'retries': row.get('retries'),
                'recommended_action': (
                    'Retry the checks when connection is restored.'
                    if code == 'MYSIM_SYNC_CHECK_UNAVAILABLE'
                    else 'Review the matching mySim movements before retrying.'
                    if code == 'MYSIM_SYNC_DUPLICATE'
                    else 'Review the prior state. GI origin differences are informational and do not block.'
                    if code == 'MYSIM_SYNC_STATE_MISMATCH'
                    else 'Correct the listed data and repeat validation.'
                ),
            },
        }
        actions.append({'action': action, 'existing_alert_id': active[0]['id'] if active else None, 'alert': alert})
    return actions


def ensure_persistence_schema(db: Any) -> None:
    """Impide escrituras parciales contra una versión de esquema incorrecta."""
    from sqlalchemy import text

    required = {
        "integration_outbox": {
            "id", "entity_id", "status", "sync_decision", "sync_reason",
            "payload_sha256", "decision_at",
        },
        "alerts": {
            "id", "code", "title", "message", "severity", "status", "source",
            "entity_type", "entity_id", "movement_id", "item_id", "epc",
            "metadata", "updated_at", "resolved_at",
        },
    }
    rows = db.execute(text("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name IN ('integration_outbox', 'alerts')
    """)).all()
    available: dict[str, set[str]] = {}
    for table_name, column_name in rows:
        available.setdefault(table_name, set()).add(column_name)
    missing = [
        f"{table}.{column}"
        for table, columns in required.items()
        for column in sorted(columns - available.get(table, set()))
    ]
    if missing:
        raise RuntimeError(
            "Esquema no preparado para guardar decisiones: " + ", ".join(missing)
        )


def write_alert_action(db: Any, preview: dict[str, Any]) -> str:
    from sqlalchemy import text

    action = preview["action"]
    if action == "MANTENER_HASTA_COMPLETAR_COMPROBACIONES":
        return "maintained"
    if action == "REVISAR_ALERTAS_DUPLICADAS":
        raise RuntimeError(
            f"Hay varias alertas activas para {preview.get('code')}; se cancela la transacción"
        )
    if action == "RESOLVER":
        result = db.execute(text("""
            UPDATE public.alerts
            SET status = 'resolved', resolved_at = now(), updated_at = now()
            WHERE id = :id
              AND code = :code
              AND status IN ('open', 'acknowledged')
        """), {"id": preview["existing_alert_id"], "code": preview["code"]})
        if result.rowcount != 1:
            raise RuntimeError("La alerta que se pretendía resolver cambió durante la comprobación")
        return "resolved"

    alert = preview.get("alert")
    if not isinstance(alert, dict):
        raise RuntimeError(f"Acción de alerta sin contenido: {action}")
    params = {
        **{key: alert.get(key) for key in (
            "code", "title", "message", "severity", "status", "source",
            "entity_type", "entity_id", "movement_id", "item_id", "epc",
        )},
        "metadata": json.dumps(alert.get("metadata") or {}, ensure_ascii=False, default=str),
    }
    active = db.execute(text("""
        SELECT id, status
        FROM public.alerts
        WHERE code = :code
          AND movement_id = :movement_id
          AND status IN ('open', 'acknowledged')
        ORDER BY id
        FOR UPDATE
    """), {"code": params["code"], "movement_id": params["movement_id"]}).mappings().all()
    if len(active) > 1:
        raise RuntimeError(
            f"Hay varias alertas activas para {params['code']} y movimiento {params['movement_id']}"
        )
    if active:
        params["id"] = active[0]["id"]
        params["status"] = active[0]["status"]
        result = db.execute(text("""
            UPDATE public.alerts
            SET title = :title, message = :message, severity = :severity,
                status = :status, source = :source, entity_type = :entity_type,
                entity_id = :entity_id, movement_id = :movement_id,
                item_id = :item_id, epc = :epc,
                metadata = CAST(:metadata AS jsonb), updated_at = now(), resolved_at = NULL
            WHERE id = :id
        """), params)
        if result.rowcount != 1:
            raise RuntimeError("La alerta activa cambió durante la actualización")
        return "updated"
    db.execute(text("""
        INSERT INTO public.alerts (
            code, title, message, severity, status, source, entity_type,
            entity_id, movement_id, item_id, epc, metadata, updated_at
        ) VALUES (
            :code, :title, :message, :severity, :status, :source, :entity_type,
            :entity_id, :movement_id, :item_id, :epc,
            CAST(:metadata AS jsonb), now()
        )
    """), params)
    return "created"


def apply_database_actions(actions: list[dict[str, Any]]) -> dict[str, int]:
    """Guarda decisiones, payloads y alertas en una transacción; nunca llama a mySim."""
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    counts = {"decisions": 0, "created": 0, "updated": 0, "resolved": 0, "maintained": 0}
    with SessionLocal.begin() as db:
        ensure_persistence_schema(db)
        for item in actions:
            decision = item["decision"]
            payload = item.get("payload")
            payload_json = None
            payload_sha256 = None
            if payload is not None:
                if not isinstance(payload, dict):
                    raise RuntimeError(
                        f"Outbox {item['outbox_id']} generó un payload que no es un objeto JSON"
                    )
                payload_sha256, _ = movement_fingerprint(payload)
                expected_sha256 = decision.get("payload_sha256")
                if expected_sha256 is not None and expected_sha256 != payload_sha256:
                    raise RuntimeError(
                        f"Outbox {item['outbox_id']} cambió de payload durante la validación"
                    )
                payload_json = json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            elif decision["status"] in {"READY_TO_SYNC", "WAITING_FOR_PREVIOUS"}:
                raise RuntimeError(
                    f"Outbox {item['outbox_id']} no puede quedar {decision['status']} sin payload"
                )
            result = db.execute(text("""
                UPDATE public.integration_outbox
                SET sync_decision = :sync_decision,
                    sync_reason = :sync_reason,
                    payload_json = COALESCE(CAST(:payload_json AS jsonb), payload_json),
                    payload_sha256 = :payload_sha256,
                    decision_at = now()
                WHERE id = :outbox_id
                  AND entity_id = :movement_id
                  AND target_system = :target_system
                  AND status = :observed_status
            """), {
                "sync_decision": decision["status"],
                "sync_reason": decision["reason"],
                "payload_json": payload_json,
                "payload_sha256": payload_sha256,
                "outbox_id": item["outbox_id"],
                "movement_id": item["movement_id"],
                "target_system": item["target_system"],
                "observed_status": item["observed_status"],
            })
            if result.rowcount != 1:
                raise RuntimeError(
                    f"Outbox {item['outbox_id']} cambió desde que fue leído; se cancela la transacción"
                )
            counts["decisions"] += 1
            for preview in item["alert_actions"]:
                outcome = write_alert_action(db, preview)
                counts[outcome] += 1
    return counts


def show_pending_movements(
    part_code: str,
    mysim_item_id: int,
    cfg: MySimConfig,
    target_system: str,
    details: bool = False,
    include_blocked: bool = False,
) -> list[dict[str, Any]]:
    print(
        f"\nOUTBOX: movimientos sin sincronizar de {part_code} "
        f"para {target_system} (fecha ASC)",
        flush=True,
    )
    rows = list_pending_movements(
        part_code,
        target_system,
        include_blocked=include_blocked,
    )
    if not rows:
        print(
            "No hay entradas pendientes para este código con action=sync "
            f"y target_system={target_system} que deban evaluarse.",
            flush=True,
        )
        return []
    print(f"Entradas: {len(rows)} | movimientos distintos: {len({r['movement_id'] for r in rows})}", flush=True)
    print("VALIDACIÓN Y CONCILIACIÓN: no hay envíos ni cambios de estado. Las coincidencias se deciden por campos de negocio; el texto solo aporta evidencia.", flush=True)
    counts = {}
    for row in rows:
        counts[row['movement_id']] = counts.get(row['movement_id'], 0) + 1
    resolver = ReferenceResolver(cfg, target_system)
    reconciler = MovementReconciler(cfg, mysim_item_id)
    database_actions = []
    alert_actions = {}
    references_ok = 0
    local_ok = 0
    payloads_built = 0
    reconciliation_counts = {
        "DUPLICADO_CONFIRMADO": 0,
        "POSIBLE_DUPLICADO": 0,
        "NO_ENCONTRADO": 0,
        "NO_DETERMINADO": 0,
    }
    decision_counts = {
        "READY_TO_SYNC": 0,
        "BLOCKED_VALIDATION": 0,
        "BLOCKED_STATE_MISMATCH": 0,
        "DUPLICATE_CONFIRMED": 0,
        "POSSIBLE_DUPLICATE": 0,
        "CHECK_UNAVAILABLE": 0,
        "WAITING_FOR_PREVIOUS": 0,
    }
    sequence_blocker_id = None
    for index, row in enumerate(rows, 1):
        validation = validate_movement(row)
        if counts[row['movement_id']] > 1:
            validation['issues'].append("Varias entradas de outbox para el mismo movimiento; revisar duplicación")
            validation['local_data_ok'] = False
        if validation['local_data_ok']:
            local_ok += 1
        state = "DATOS_LOCALES_OK" if validation['local_data_ok'] else "FALTAN_DATOS_O_REVISION"
        print(f"\n[{index}] outbox={row['outbox_id']} | movimiento={row['movement_id']} | estado={row['outbox_status']} | {state}", flush=True)
        print(f"  Fecha: {row['movement_date']} | tipo={row['movement_type']} (mySim={validation['mysim_movement_type_id']}) | cantidad={row['quantity']}", flush=True)
        print(f"  Item local={row['local_item_id']} | origen={row['from_location_id']} | destino={row['to_location_id']} | autor mySim={(row.get('movement_data') or {}).get('mysim_user_id')}", flush=True)
        print(f"  Reintentos históricos={row['retries']} | próximo reintento={row['next_retry_at']}", flush=True)
        for issue in validation['issues']:
            print(f"  REVISAR: {issue}", flush=True)
        for wait in validation['waits']:
            print(f"  ESPERA: {wait}", flush=True)
        references = resolve_references(row, resolver)
        all_verified = (
            references['user']['status'] == 'VERIFICADO'
            and references['destination']['status'] == 'VERIFICADO'
        )
        for side, label, id_field in [('source', 'origen', 'from_location_id'), ('destination', 'destino', 'to_location_id')]:
            ref = references[side]
            if row.get(id_field) is None:
                continue
            if side == 'destination' and ref['status'] != 'VERIFICADO':
                all_verified = False
            print(f"  UBICACIÓN {label}: local={row[id_field]} | código={ref.get('local_code')} | mySim={ref.get('id')} | {ref['status']}", flush=True)
            if ref.get('detail'):
                print(f"    {ref['detail']}", flush=True)
        user_ref = references['user']
        user_name = (user_ref.get('row') or {}).get('fullName')
        print(f"  AUTOR: mySim={user_ref.get('id')} | nombre={user_name} | {user_ref['status']}", flush=True)
        if user_ref.get('detail'):
            print(f"    {user_ref['detail']}", flush=True)
        payload = None
        payload_error = None
        reconciliation = None
        prior_state = None
        if all_verified and validation['local_data_ok']:
            try:
                payload = build_mysim_payload(
                    mysim_item_id=mysim_item_id,
                    row=row,
                    validation=validation,
                    references=references,
                )
                payloads_built += 1
            except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
                payload_error = str(exc)
        if payload is not None:
            print("  PAYLOAD: CONSTRUIDO (simulación; no enviado)", flush=True)
            print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
            payload_sha256, _ = movement_fingerprint(payload)
            print(f"  HUELLA SHA-256: {payload_sha256}", flush=True)
            if sequence_blocker_id is None:
                prior_state = reconciler.check_prior_state(payload)
                print(
                    f"  ESTADO ANTERIOR: {prior_state['status']} | {prior_state['reason']}",
                    flush=True,
                )
                reconciliation = reconciler.check(payload)
                reconciliation_counts[reconciliation['status']] += 1
                print(
                    f"  CONCILIACIÓN: {reconciliation['status']} | {reconciliation['reason']}",
                    flush=True,
                )
                for match in reconciliation.get('matches', []):
                    print(
                        f"    candidato mySim id={match.get('mysim_id')} | "
                        f"movementId={match.get('movementId')} | fecha={match.get('date')}",
                        flush=True,
                    )
            else:
                print(
                    f"  CONCILIACIÓN: POSPUESTA por el movimiento anterior {sequence_blocker_id}",
                    flush=True,
                )
            if details:
                print("  PETICIÓN HTTP PREVISTA (simulación):", flush=True)
                print(json.dumps(build_request_preview(mysim_item_id, payload), ensure_ascii=False, indent=2), flush=True)
                if reconciliation:
                    print("  EVIDENCIA DE CONCILIACIÓN:", flush=True)
                    print(json.dumps(reconciliation, ensure_ascii=False, indent=2, default=str), flush=True)
                if prior_state:
                    print("  EVIDENCIA DEL ESTADO ANTERIOR:", flush=True)
                    print(json.dumps(prior_state, ensure_ascii=False, indent=2, default=str), flush=True)
        elif payload_error:
            print(f"  PAYLOAD: BLOQUEADO | {payload_error}", flush=True)
        else:
            print("  PAYLOAD: BLOQUEADO por validación local o referencias mySim", flush=True)
        decision = decide_movement(
            row=row,
            validation=validation,
            references=references,
            payload=payload,
            payload_error=payload_error,
            reconciliation=reconciliation,
            prior_state=prior_state,
            previous_blocker_id=sequence_blocker_id,
        )
        decision_counts[decision['status']] += 1
        print(f"  DECISIÓN: {decision['status']} | {decision['reason']}", flush=True)
        if sequence_blocker_id is None and decision['blocks_following']:
            sequence_blocker_id = row['movement_id']
        previews = plan_sync_alerts(row, validation, references, reconciliation, prior_state)
        database_actions.append({
            "outbox_id": row["outbox_id"],
            "movement_id": row["movement_id"],
            "target_system": row["target_system"],
            "observed_status": row["outbox_status"],
            "decision": decision,
            "payload": payload,
            "alert_actions": previews,
        })
        for preview in previews:
            key = (row['movement_id'], (preview.get('alert') or preview).get('code'))
            alert_actions[key] = preview
        print(f"  ALERTAS (simulación): {len(previews)} acciones propuestas", flush=True)
        for preview in previews:
            alert = preview.get('alert') or {}
            print(f"    {preview['action']} | {alert.get('code') or preview.get('code')} | alerta existente={preview.get('existing_alert_id')}", flush=True)
            if alert:
                print(f"    {alert['title']} | severidad={alert['severity']} | estado={alert['status']}", flush=True)
            if details:
                print(json.dumps(preview, ensure_ascii=False, indent=2, default=str), flush=True)
        if all_verified and validation['local_data_ok']:
            references_ok += 1
        for pending in validation['pending']:
            if pending.startswith(('Comprobar usuario', 'Resolver ubicación')):
                continue
            print(f"  COMPROBACIÓN PENDIENTE: {pending}", flush=True)
        if details:
            print("  DECISIÓN COMPLETA:", flush=True)
            print(json.dumps(decision, ensure_ascii=False, indent=2, default=str), flush=True)
            print(json.dumps(row, ensure_ascii=False, indent=2, default=str), flush=True)
    print(f"\nRESUMEN: {local_ok}/{len(rows)} entradas con datos locales completos; {len(rows)-local_ok} requieren revisión.", flush=True)
    print(f"Datos locales y referencias guardadas verificados: {references_ok}/{len(rows)}.", flush=True)
    print(f"Payloads construidos (sin enviar): {payloads_built}/{len(rows)}.", flush=True)
    if payloads_built:
        print(
            "Conciliación mySim: "
            + " | ".join(f"{status}={count}" for status, count in reconciliation_counts.items()),
            flush=True,
        )
    else:
        print("Conciliación mySim: no ejecutada; ningún movimiento superó las comprobaciones previas.", flush=True)
    print(
        "Decisiones: "
        + " | ".join(f"{status}={count}" for status, count in decision_counts.items()),
        flush=True,
    )
    print(f"Alertas propuestas (sin guardar): {len(alert_actions)}.", flush=True)
    print(
        f"Candidatos READY_TO_SYNC: {decision_counts['READY_TO_SYNC']}. "
        "Preparadas para envío real: 0; el envío sigue desactivado.",
        flush=True,
    )
    return database_actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprobar y simular movimientos mySim (solo lectura).")
    parser.add_argument("--part-code", required=True, help="Código exacto del artículo (partId).")
    parser.add_argument(
        "--details",
        action="store_true",
        help="Mostrar la petición HTTP prevista, alertas y datos locales completos.",
    )
    parser.add_argument(
        "--apply-db-actions",
        action="store_true",
        help="Guardar decisiones y alertas locales. No envía movimientos a mySim.",
    )
    parser.add_argument(
        "--reevaluate-blocked",
        action="store_true",
        help=(
            "Volver a evaluar entradas BLOCKED_VALIDATION después de corregir "
            "sus datos. No incluye DUPLICATE_CONFIRMED."
        ),
    )
    args = parser.parse_args()
    if args.apply_db_actions and os.getenv(DB_WRITE_CONFIRMATION_ENV) != DB_WRITE_CONFIRMATION_VALUE:
        print(
            "ERROR: escritura local bloqueada. Además de --apply-db-actions debe definirse "
            f"{DB_WRITE_CONFIRMATION_ENV}={DB_WRITE_CONFIRMATION_VALUE}.",
            file=sys.stderr,
        )
        return 2
    if args.apply_db_actions:
        print(
            "MODO ESCRITURA LOCAL: se guardarán decisiones y alertas; el envío a mySim continúa desactivado.",
            flush=True,
        )
    try:
        target_system = get_mysim_target_system()
        cfg = MySimConfig.from_env()
        item = find_item(cfg, args.part_code)
    except requests.RequestException as exc:
        # No imprimir la excepción completa: puede contener detalles de la petición.
        print(f"ERROR: Fallo de conexión ({type(exc).__name__}); existencia no determinada.", file=sys.stderr)
        return 2
    except (LookupError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if item is None:
        print("SIN COINCIDENCIAS: mySim respondió correctamente y no devolvió el artículo.")
        return 1
    print(f"ENCONTRADO: partId={item['partId']} | mySim id={item['id']}")
    print(json.dumps(item, ensure_ascii=False, indent=2), flush=True)
    try:
        movement = get_last_movement(cfg, int(item["id"]))
    except LookupError as exc:
        print(f"ERROR AL CONSULTAR MOVIMIENTOS: {exc}", file=sys.stderr)
        return 2
    if movement is None:
        print("SIN MOVIMIENTOS: consulta válida sin resultados para este artículo.", flush=True)
    else:
        print(f"ÚLTIMO MOVIMIENTO: id={movement['id']} | fecha={movement['date']}", flush=True)
        print(json.dumps(movement, ensure_ascii=False, indent=2), flush=True)
    try:
        database_actions = show_pending_movements(
            args.part_code,
            int(item["id"]),
            cfg,
            target_system,
            details=args.details,
            include_blocked=args.reevaluate_blocked,
        )
    except Exception as exc:
        # SQLAlchemy puede incluir credenciales/parámetros en errores completos.
        print(f"ERROR AL LEER OUTBOX: {type(exc).__name__}. Revisar conexión y esquema local. No se modificó la cola.", file=sys.stderr)
        return 2
    if not args.apply_db_actions:
        print("MODO SIMULACIÓN: las decisiones y alertas anteriores no se han guardado.", flush=True)
        return 0
    try:
        write_counts = apply_database_actions(database_actions)
    except RuntimeError as exc:
        print(f"ERROR AL GUARDAR: {exc}. Transacción cancelada.", file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            f"ERROR AL GUARDAR: {type(exc).__name__}. Transacción cancelada; revisar esquema y conexión.",
            file=sys.stderr,
        )
        return 2
    print(
        "CAMBIOS LOCALES GUARDADOS: "
        + " | ".join(f"{key}={value}" for key, value in write_counts.items()),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nConsulta detenida por el usuario.", flush=True)
        raise SystemExit(130)
