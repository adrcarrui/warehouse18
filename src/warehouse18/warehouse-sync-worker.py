import os
import json
import time
import traceback
from typing import Any, Dict

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DBAPIError


# =========================
# Configuración
# =========================
DSN = os.environ.get(
    "WAREHOUSE18_DSN",
    "postgresql://warehouse18_user:CHANGE_ME@127.0.0.1:5432/warehouse18",
)

POLL_SECONDS = 2.0
MAX_RETRIES = 5            # <- AQUÍ decides cuántas veces reintentar
BASE_BACKOFF_SECONDS = 5   # <- base del backoff

TZ = "Europe/Madrid"


# =========================
# SQL
# =========================
PICK_SQL = """
WITH picked AS (
  SELECT id
  FROM integration_outbox
  WHERE status = 'pending'
    AND (next_retry_at IS NULL OR next_retry_at <= now())
  ORDER BY created_at
  FOR UPDATE SKIP LOCKED
  LIMIT 50
)
SELECT o.id, o.entity_type, o.entity_id, o.action, o.payload_json, o.retries
FROM integration_outbox o
JOIN picked p ON p.id = o.id
ORDER BY o.created_at;
"""

MARK_SENT_SQL = """
UPDATE integration_outbox
SET status = 'sent',
    last_attempt_at = now()
WHERE id = :id;
"""

# Nota: hacemos cast a interval para que el bind param funcione siempre
MARK_RETRY_SQL = """
UPDATE integration_outbox
SET status = 'pending',
    retries = retries + 1,
    last_attempt_at = now(),
    next_retry_at = now() + (:base_interval::interval * (retries + 1))
WHERE id = :id;
"""

MARK_FAILED_SQL = """
UPDATE integration_outbox
SET status = 'failed',
    last_attempt_at = now()
WHERE id = :id;
"""

LOG_ERROR_SQL = """
INSERT INTO error_log (
  severity, source, operation, entity_type, entity_id, message, metadata_json
)
VALUES ('error', 'warehouse-sync-worker', 'outbox_send', :entity_type, :entity_id, :message, :metadata_json::jsonb);
"""


# =========================
# API placeholder
# =========================
def send_to_api(
    entity_type: str,
    entity_id: int,
    action: str,
    payload: Dict[str, Any],
) -> None:
    """
    Aquí va tu integración real (requests.post, etc.)
    Lanza excepción si falla.
    """
    # Simulación: fuerza fallo si la acción contiene 'fail'
    if "fail" in action:
        raise RuntimeError("Simulated API failure")

    # En producción:
    # response = requests.post(URL, json=payload, timeout=5)
    # if response.status_code not in (200, 201, 204):
    #     raise RuntimeError(f"API error {response.status_code}")

    return


# =========================
# SQLAlchemy setup
# =========================
engine = create_engine(
    DSN,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# =========================
# Worker loop
# =========================
def main() -> None:
    print("[warehouse-sync-worker] started")

    pick_stmt = text(PICK_SQL)
    mark_sent_stmt = text(MARK_SENT_SQL)
    mark_retry_stmt = text(MARK_RETRY_SQL)
    mark_failed_stmt = text(MARK_FAILED_SQL)
    log_error_stmt = text(LOG_ERROR_SQL)
    set_tz_stmt = text(f"SET timezone TO '{TZ}';")

    base_interval = f"{BASE_BACKOFF_SECONDS} seconds"

    while True:
        processed_any = False

        # 1 sesión por iteración: bloquea, procesa, commitea o rollback.
        db = SessionLocal()
        try:
            db.execute(set_tz_stmt)

            # Mantiene el mismo comportamiento que tu psycopg:
            # selecciona + marca sent/retry/failed dentro de la misma transacción.
            with db.begin():
                rows = db.execute(pick_stmt).all()

                for (
                    outbox_id,
                    entity_type,
                    entity_id,
                    action,
                    payload_json,
                    retries,
                ) in rows:
                    processed_any = True

                    try:
                        payload = (
                            payload_json
                            if isinstance(payload_json, dict)
                            else json.loads(payload_json)
                        )

                        send_to_api(entity_type, entity_id, action, payload)

                        db.execute(mark_sent_stmt, {"id": outbox_id})
                        print(f"[warehouse-sync-worker] SENT id={outbox_id} action={action}")

                    except Exception as e:
                        # ⛔ Límite de reintentos alcanzado
                        if retries >= MAX_RETRIES:
                            db.execute(mark_failed_stmt, {"id": outbox_id})
                            print(
                                f"[warehouse-sync-worker] FAILED id={outbox_id} "
                                f"action={action} retries={retries}"
                            )
                        else:
                            # 🔁 Reintento con backoff
                            db.execute(
                                mark_retry_stmt,
                                {"id": outbox_id, "base_interval": base_interval},
                            )
                            print(
                                f"[warehouse-sync-worker] RETRY id={outbox_id} "
                                f"action={action} retries={retries + 1}"
                            )

                        meta = {
                            "outbox_id": outbox_id,
                            "action": action,
                            "retries_before": retries,
                            "exception": repr(e),
                            "traceback": traceback.format_exc(),
                            "payload": payload_json,
                        }

                        db.execute(
                            log_error_stmt,
                            {
                                "entity_type": entity_type,
                                "entity_id": entity_id,
                                "message": str(e)[:500],
                                "metadata_json": json.dumps(meta),
                            },
                        )

            # Si no hubo rows, no hace falta esperar dentro del begin.
        except DBAPIError as e:
            # SQLAlchemy envuelve errores DB, deja registro simple y sigue.
            db.rollback()
            print("[warehouse-sync-worker] DBAPIError:", repr(e))
        finally:
            db.close()

        if not processed_any:
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
