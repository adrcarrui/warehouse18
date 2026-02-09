import subprocess
import os
import sys

# ===== CONFIGURACIÓN =====
PG_DUMP = r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"  # ajusta versión/ruta
HOST = "localhost"
PORT = "5432"
USER = "postgres"
DB_NAME = "warehouse18"
OUTPUT_FILE = "warehouse18_schema.sql"

# Si no quieres que te pida password:
# set PG_PASSWORD como variable de entorno antes de ejecutar
# os.environ["PGPASSWORD"] = "tu_password"

cmd = [
    PG_DUMP,
    "-h", HOST,
    "-p", PORT,
    "-U", USER,
    "-d", DB_NAME,
    "--schema-only",
]

try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        subprocess.run(
            cmd,
            stdout=f,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )

    print(f"Schema dump generado correctamente: {OUTPUT_FILE}")

except subprocess.CalledProcessError as e:
    print("Error ejecutando pg_dump")
    print(e.stderr)
    sys.exit(1)
