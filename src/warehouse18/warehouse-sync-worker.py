import os
import json
import time
import traceback
from typing import Any, Dict

import psycopg


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
WHERE id = %s;
"""

MARK_RETRY_SQL = """
UPDATE integration_outbox
SET status = 'pending',
    retries = retries + 1,
    last_attempt_at = now(),
    next_retry_at = now() + (%s * (retries + 1))
WHERE id = %s;
"""

MARK_FAILED_SQL = """
UPDATE integration_outbox
SET status = 'failed',
    last_attempt_at = now()
WHERE id = %s;
"""

LOG_ERROR_SQL = """
INSERT INTO error_log (
  severity, source, operation, entity_type, entity_id, message, metadata_json
)
VALUES ('error', 'warehouse-sync-worker', 'outbox_send', %s, %s, %s, %s::jsonb);
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
# Worker loop
# =========================
def main() -> None:
    print("[warehouse-sync-worker] started")

    while True:
        processed_any = False

        with psycopg.connect(DSN) as conn:
            conn.execute("SET timezone TO 'Europe/Madrid';")

            with conn.transaction():
                rows = conn.execute(PICK_SQL).fetchall()

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

                        conn.execute(MARK_SENT_SQL, (outbox_id,))
                        print(
                            f"[warehouse-sync-worker] SENT id={outbox_id} action={action}"
                        )

                    except Exception as e:
                        # ⛔ Límite de reintentos alcanzado
                        if retries >= MAX_RETRIES:
                            conn.execute(MARK_FAILED_SQL, (outbox_id,))
                            print(
                                f"[warehouse-sync-worker] FAILED id={outbox_id} "
                                f"action={action} retries={retries}"
                            )

                        else:
                            # 🔁 Reintento con backoff
                            conn.execute(
                                MARK_RETRY_SQL,
                                (
                                    f"{BASE_BACKOFF_SECONDS} seconds",
                                    outbox_id,
                                ),
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

                        conn.execute(
                            LOG_ERROR_SQL,
                            (
                                entity_type,
                                entity_id,
                                str(e)[:500],
                                json.dumps(meta),
                            ),
                        )

        if not processed_any:
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
