import json
import psycopg2
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / "mysim_locations_code_to_single_id.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [
    (name.strip().upper(), str(mysim_code))
    for name, mysim_code in data.items()
]

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="warehouse18",
    user="postgres",
    password="admin",
)

conn.autocommit = False

try:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TEMP TABLE tmp_location_codes (
                name TEXT PRIMARY KEY,
                mysim_code TEXT NOT NULL
            ) ON COMMIT DROP;
        """)

        cur.executemany("""
            INSERT INTO tmp_location_codes (name, mysim_code)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE
            SET mysim_code = EXCLUDED.mysim_code;
        """, rows)

        cur.execute("""
            UPDATE locations l
            SET code = t.mysim_code
            FROM tmp_location_codes t
            WHERE UPPER(TRIM(l.name)) = t.name;
        """)

        print("Updated locations:", cur.rowcount)

    conn.commit()

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()