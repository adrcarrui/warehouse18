"""Transiciones transaccionales del outbox para el futuro worker mySim.

Este módulo no contiene ninguna llamada HTTP. Su CLI solo inspecciona; las
funciones de escritura están destinadas al worker que realizará el envío.
Requiere las columnas de warehouse-sync-state-migration.sql.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from dotenv import load_dotenv


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


@dataclass(frozen=True)
class RuntimeConfig:
    lease_seconds: int = 120
    max_retries: int = 5
    base_backoff_seconds: int = 30

    def validate(self) -> None:
        if self.lease_seconds < 30:
            raise ValueError("lease_seconds debe ser al menos 30")
        if self.max_retries < 1:
            raise ValueError("max_retries debe ser al menos 1")
        if self.base_backoff_seconds < 1:
            raise ValueError("base_backoff_seconds debe ser positivo")


@dataclass(frozen=True)
class OutboxClaim:
    outbox_id: int
    movement_id: int
    target_system: str
    attempt_token: str
    worker_id: str
    payload_json: dict[str, Any]
    retries: int
    lease_expires_at: Any


REQUIRED_COLUMNS = {
    "id", "direction", "target_system", "entity_type", "entity_id",
    "action", "payload_json", "status", "retries", "last_attempt_at",
    "next_retry_at", "last_error", "sync_decision", "sync_reason",
    "payload_sha256", "decision_at", "attempt_token", "claimed_by",
    "claimed_at", "lease_expires_at", "sent_at", "reconciled_at",
    "remote_id", "response_json",
}


def default_worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def ensure_runtime_schema(db: Any) -> None:
    from sqlalchemy import text

    columns = {
        row[0]
        for row in db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'integration_outbox'
        """)).all()
    }
    missing = sorted(REQUIRED_COLUMNS - columns)
    if missing:
        raise RuntimeError(
            "Falta aplicar warehouse-sync-state-migration.sql. Columnas ausentes: "
            + ", ".join(missing)
        )


def inspect_runtime_state(target_system: str | None = None) -> dict[str, Any]:
    """Resumen de solo lectura; no bloquea ni reclama entradas."""
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    target_system = target_system or get_mysim_target_system()
    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        try:
            ensure_runtime_schema(db)
            summary = db.execute(text("""
                SELECT status, sync_decision, COUNT(*) AS total
                FROM public.integration_outbox
                WHERE direction = 'outbound'
                  AND target_system = :target_system
                  AND entity_type = 'movement'
                  AND action = 'sync'
                GROUP BY status, sync_decision
                ORDER BY status, sync_decision NULLS FIRST
            """), {"target_system": target_system}).mappings().all()
            next_candidate = db.execute(text("""
                SELECT id AS outbox_id, entity_id AS movement_id, status,
                       retries, next_retry_at, created_at, payload_sha256
                FROM public.integration_outbox
                WHERE direction = 'outbound'
                  AND target_system = :target_system
                  AND entity_type = 'movement'
                  AND action = 'sync'
                  AND status IN ('pending', 'error')
                  AND sync_decision = 'READY_TO_SYNC'
                  AND (next_retry_at IS NULL OR next_retry_at <= now())
                ORDER BY next_retry_at NULLS FIRST, created_at, id
                LIMIT 1
            """), {"target_system": target_system}).mappings().first()
            expired = db.execute(text("""
                SELECT id AS outbox_id, entity_id AS movement_id,
                       claimed_by, claimed_at, lease_expires_at, attempt_token
                FROM public.integration_outbox
                WHERE direction = 'outbound'
                  AND target_system = :target_system
                  AND entity_type = 'movement'
                  AND action = 'sync'
                  AND status = 'processing'
                  AND lease_expires_at IS NOT NULL
                  AND lease_expires_at <= now()
                ORDER BY lease_expires_at, id
            """), {"target_system": target_system}).mappings().all()
            return {
                "target_system": target_system,
                "summary": [dict(row) for row in summary],
                "next_candidate": dict(next_candidate) if next_candidate else None,
                "expired_leases": [dict(row) for row in expired],
            }
        finally:
            db.rollback()


def claim_next_ready(
    *,
    worker_id: str,
    target_system: str | None = None,
    config: RuntimeConfig = RuntimeConfig(),
) -> OutboxClaim | None:
    """Reclama una entrada mediante SKIP LOCKED y devuelve su token de intento."""
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    config.validate()
    target_system = target_system or get_mysim_target_system()
    attempt_token = str(uuid.uuid4())
    with SessionLocal.begin() as db:
        ensure_runtime_schema(db)
        row = db.execute(text("""
            WITH candidate AS (
                SELECT id
                FROM public.integration_outbox
                WHERE direction = 'outbound'
                  AND target_system = :target_system
                  AND entity_type = 'movement'
                  AND action = 'sync'
                  AND status IN ('pending', 'error')
                  AND sync_decision = 'READY_TO_SYNC'
                  AND (next_retry_at IS NULL OR next_retry_at <= now())
                ORDER BY next_retry_at NULLS FIRST, created_at, id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE public.integration_outbox AS o
            SET status = 'processing',
                attempt_token = CAST(:attempt_token AS uuid),
                claimed_by = :worker_id,
                claimed_at = now(),
                lease_expires_at = now() + make_interval(secs => :lease_seconds),
                last_attempt_at = now(),
                last_error = NULL
            FROM candidate
            WHERE o.id = candidate.id
            RETURNING o.id AS outbox_id, o.entity_id AS movement_id,
                      o.target_system,
                      o.payload_json, o.retries, o.lease_expires_at
        """), {
            "attempt_token": attempt_token,
            "worker_id": worker_id,
            "target_system": target_system,
            "lease_seconds": float(config.lease_seconds),
        }).mappings().first()
        if row is None:
            return None
        payload = row["payload_json"]
        if not isinstance(payload, dict):
            raise RuntimeError(f"Outbox {row['outbox_id']} contiene payload_json inválido")
        return OutboxClaim(
            outbox_id=int(row["outbox_id"]),
            movement_id=int(row["movement_id"]),
            target_system=str(row["target_system"]),
            attempt_token=attempt_token,
            worker_id=worker_id,
            payload_json=payload,
            retries=int(row["retries"]),
            lease_expires_at=row["lease_expires_at"],
        )


def claim_ready_by_id(
    *,
    outbox_id: int,
    expected_movement_id: int,
    expected_payload_sha256: str,
    worker_id: str,
    target_system: str | None = None,
    config: RuntimeConfig = RuntimeConfig(),
) -> OutboxClaim | None:
    """Reclama una entrada concreta solo si conserva todos los valores esperados."""
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    config.validate()
    target_system = target_system or get_mysim_target_system()
    if outbox_id <= 0 or expected_movement_id <= 0:
        raise ValueError("Los IDs esperados deben ser positivos")
    expected_payload_sha256 = expected_payload_sha256.strip().lower()
    if len(expected_payload_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in expected_payload_sha256
    ):
        raise ValueError("expected_payload_sha256 no es una huella SHA-256 válida")

    attempt_token = str(uuid.uuid4())
    with SessionLocal.begin() as db:
        ensure_runtime_schema(db)
        row = db.execute(text("""
            UPDATE public.integration_outbox
            SET status = 'processing',
                attempt_token = CAST(:attempt_token AS uuid),
                claimed_by = :worker_id,
                claimed_at = now(),
                lease_expires_at = now() + make_interval(secs => :lease_seconds),
                last_attempt_at = now(),
                last_error = NULL
            WHERE id = :outbox_id
              AND entity_id = :movement_id
              AND direction = 'outbound'
              AND target_system = :target_system
              AND entity_type = 'movement'
              AND action = 'sync'
              AND status IN ('pending', 'error')
              AND sync_decision = 'READY_TO_SYNC'
              AND payload_sha256 = :payload_sha256
              AND payload_json IS NOT NULL
              AND payload_json <> '{}'::jsonb
              AND remote_id IS NULL
              AND sent_at IS NULL
              AND (next_retry_at IS NULL OR next_retry_at <= now())
            RETURNING id AS outbox_id, entity_id AS movement_id,
                      target_system, payload_json, retries, lease_expires_at
        """), {
            "outbox_id": outbox_id,
            "movement_id": expected_movement_id,
            "target_system": target_system,
            "payload_sha256": expected_payload_sha256,
            "attempt_token": attempt_token,
            "worker_id": worker_id,
            "lease_seconds": float(config.lease_seconds),
        }).mappings().first()
        if row is None:
            return None
        payload = row["payload_json"]
        if not isinstance(payload, dict):
            raise RuntimeError(f"Outbox {row['outbox_id']} contiene payload_json inválido")
        return OutboxClaim(
            outbox_id=int(row["outbox_id"]),
            movement_id=int(row["movement_id"]),
            target_system=str(row["target_system"]),
            attempt_token=attempt_token,
            worker_id=worker_id,
            payload_json=payload,
            retries=int(row["retries"]),
            lease_expires_at=row["lease_expires_at"],
        )


def renew_lease(
    claim: OutboxClaim,
    *,
    config: RuntimeConfig = RuntimeConfig(),
) -> None:
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    config.validate()
    with SessionLocal.begin() as db:
        result = db.execute(text("""
            UPDATE public.integration_outbox
            SET lease_expires_at = now() + make_interval(secs => :lease_seconds)
            WHERE id = :outbox_id
              AND target_system = :target_system
              AND status = 'processing'
              AND attempt_token = CAST(:attempt_token AS uuid)
              AND claimed_by = :worker_id
              AND lease_expires_at > now()
        """), {
            "lease_seconds": float(config.lease_seconds),
            "outbox_id": claim.outbox_id,
            "target_system": claim.target_system,
            "attempt_token": claim.attempt_token,
            "worker_id": claim.worker_id,
        })
        if result.rowcount != 1:
            raise RuntimeError("No se pudo renovar el lease; la reclamación ya no pertenece al worker")


def complete_sent(
    claim: OutboxClaim,
    *,
    remote_id: str,
    response: dict[str, Any],
    reconciled: bool,
) -> None:
    """Finaliza por respuesta confirmada o por duplicado reconciliado."""
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    if not str(remote_id).strip():
        raise ValueError("remote_id es obligatorio para finalizar como sent")
    with SessionLocal.begin() as db:
        result = db.execute(text("""
            UPDATE public.integration_outbox
            SET status = 'sent', sent_at = now(),
                reconciled_at = CASE WHEN :reconciled THEN now() ELSE reconciled_at END,
                remote_id = :remote_id,
                response_json = CAST(:response_json AS jsonb),
                next_retry_at = NULL, last_error = NULL,
                claimed_by = NULL, claimed_at = NULL,
                lease_expires_at = NULL, attempt_token = NULL
            WHERE id = :outbox_id
              AND target_system = :target_system
              AND status = 'processing'
              AND attempt_token = CAST(:attempt_token AS uuid)
              AND claimed_by = :worker_id
              AND lease_expires_at > now()
        """), {
            "reconciled": reconciled,
            "remote_id": str(remote_id),
            "response_json": json.dumps(response, ensure_ascii=False, default=str),
            "outbox_id": claim.outbox_id,
            "target_system": claim.target_system,
            "attempt_token": claim.attempt_token,
            "worker_id": claim.worker_id,
        })
        if result.rowcount != 1:
            raise RuntimeError("No se pudo finalizar: token de intento o propietario no coinciden")


def complete_error(
    claim: OutboxClaim,
    *,
    error: str,
    delivery_uncertain: bool,
    config: RuntimeConfig = RuntimeConfig(),
) -> None:
    """Programa reintento o exige conciliación si el POST pudo llegar a mySim."""
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    config.validate()
    with SessionLocal.begin() as db:
        result = db.execute(text("""
            UPDATE public.integration_outbox
            SET status = 'error', retries = retries + 1,
                last_error = :error,
                sync_decision = CASE
                    WHEN :delivery_uncertain OR retries + 1 >= :max_retries
                        THEN 'CHECK_UNAVAILABLE'
                    ELSE sync_decision
                END,
                sync_reason = CASE
                    WHEN :delivery_uncertain
                        THEN 'Resultado del envío incierto; conciliar antes de reintentar'
                    WHEN retries + 1 >= :max_retries
                        THEN 'Máximo de reintentos alcanzado; requiere revisión'
                    ELSE sync_reason
                END,
                decision_at = CASE
                    WHEN :delivery_uncertain OR retries + 1 >= :max_retries
                        THEN now()
                    ELSE decision_at
                END,
                next_retry_at = CASE
                    WHEN :delivery_uncertain OR retries + 1 >= :max_retries THEN NULL
                    ELSE now() + make_interval(
                        secs => :base_backoff_seconds * power(2, LEAST(retries, 10))
                    )
                END,
                claimed_by = NULL, claimed_at = NULL,
                lease_expires_at = NULL, attempt_token = NULL
            WHERE id = :outbox_id
              AND target_system = :target_system
              AND status = 'processing'
              AND attempt_token = CAST(:attempt_token AS uuid)
              AND claimed_by = :worker_id
              AND lease_expires_at > now()
        """), {
            "error": str(error)[:2000],
            "delivery_uncertain": delivery_uncertain,
            "max_retries": config.max_retries,
            "base_backoff_seconds": float(config.base_backoff_seconds),
            "outbox_id": claim.outbox_id,
            "target_system": claim.target_system,
            "attempt_token": claim.attempt_token,
            "worker_id": claim.worker_id,
        })
        if result.rowcount != 1:
            raise RuntimeError("No se pudo registrar el error: la reclamación ya no pertenece al worker")


def recover_expired_leases(target_system: str | None = None) -> int:
    """Un lease caducado se considera entrega incierta y obliga a conciliar."""
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    target_system = target_system or get_mysim_target_system()
    with SessionLocal.begin() as db:
        ensure_runtime_schema(db)
        result = db.execute(text("""
            UPDATE public.integration_outbox
            SET status = 'error', retries = retries + 1,
                last_error = 'Lease caducado; resultado del intento desconocido',
                sync_decision = 'CHECK_UNAVAILABLE',
                sync_reason = 'El worker perdió el lease; conciliar con mySim antes de reintentar',
                decision_at = now(), next_retry_at = NULL,
                claimed_by = NULL, claimed_at = NULL,
                lease_expires_at = NULL, attempt_token = NULL
            WHERE direction = 'outbound'
              AND target_system = :target_system
              AND entity_type = 'movement'
              AND action = 'sync'
              AND status = 'processing'
              AND lease_expires_at IS NOT NULL
              AND lease_expires_at <= now()
        """), {"target_system": target_system})
        return int(result.rowcount or 0)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspeccionar el runtime del outbox mySim (solo lectura)."
    )
    parser.add_argument("--inspect", action="store_true", help="Mostrar candidato y leases caducados.")
    args = parser.parse_args()
    if not args.inspect:
        parser.error("Por ahora la CLI solo admite --inspect; no realiza transiciones.")
    try:
        target_system = get_mysim_target_system()
        state = inspect_runtime_state(target_system)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}; revisar conexión y esquema.", file=sys.stderr)
        return 2
    print(json.dumps(state, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
