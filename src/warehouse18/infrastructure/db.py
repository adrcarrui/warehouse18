# src/warehouse18_api/db.py
import os
import psycopg

DSN = os.environ.get("WAREHOUSE18_DSN")  # úsalo como ya hiciste con el worker
if not DSN:
    raise RuntimeError("WAREHOUSE18_DSN env var is required")

def get_conn():
    # autocommit False: cada request va en transacción
    return psycopg.connect(DSN)
