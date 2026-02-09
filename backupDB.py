import subprocess
from datetime import datetime
from pathlib import Path
import os

PG_DUMP = r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"

if not os.path.exists(PG_DUMP):
    raise FileNotFoundError(f"No existe pg_dump en: {PG_DUMP}")

DB_NAME = "warehouse18"
DB_USER = "postgres"
DB_PASSWORD = "admin"          # ← AQUÍ
DB_HOST = "127.0.0.1"
DB_PORT = "5432"

BACKUP_DIR = Path(r"C:\Users\adrian\SIA\projects")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = BACKUP_DIR / f"backup_{DB_NAME}_{timestamp}.sql"

cmd = [
    PG_DUMP,
    "-h", DB_HOST,
    "-p", DB_PORT,
    "-U", DB_USER,
    "-F", "p",
    "-f", str(backup_file),
    DB_NAME
]

env = os.environ.copy()
env["PGPASSWORD"] = DB_PASSWORD

subprocess.run(
    " ".join(f'"{c}"' for c in cmd),
    check=True,
    shell=True,
    env=env
)

print("Backup creado en:", backup_file)
