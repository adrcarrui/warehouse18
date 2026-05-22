import json
import os
from pathlib import Path

import psycopg


try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "mysim_locations_code_to_single_id.json"

RAW_DATABASE_URL = (
    os.getenv("WAREHOUSE18_DATABASE_URL")
    or os.getenv("WAREHOUSE18_DSN")
    or os.getenv("DATABASE_URL")
    or "postgresql://postgres:admin@127.0.0.1:5432/warehouse18"
)

DATABASE_URL = RAW_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

# Primero dejar en True. Solo muestra lo que haría.
# Cuando lo revises, cambia a False.
DRY_RUN = False

LETTERS = ["A", "B", "C", "D", "E", "F"]


# ============================================================
# JSON
# ============================================================

def load_mysim_locations(path: Path) -> dict[str, int]:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe el fichero:\n{path}\n\n"
            f"Coloca mysim_locations_code_to_single_id.json en esta carpeta:\n{BASE_DIR}"
        )

    with path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    result: dict[str, int] = {}

    for code, mysim_id in raw_data.items():
        normalized_code = str(code).strip().upper()

        if not normalized_code:
            continue

        try:
            result[normalized_code] = int(mysim_id)
        except (TypeError, ValueError):
            print(f"Ignorado valor inválido: {code} -> {mysim_id}")

    return result


# ============================================================
# GENERACIÓN DE LOCALIZACIONES OBJETIVO
# ============================================================

def build_target_locations(mysim_locations: dict[str, int]) -> tuple[list[dict], list[str]]:
    targets: list[dict] = []
    missing: list[str] = []

    def add_range(
        *,
        prefix: str,
        rack_start: int,
        rack_end: int,
        aisle_code: str,
    ) -> None:
        for rack_number in range(rack_start, rack_end + 1):
            for shelf_code in LETTERS:
                code = f"{prefix} {rack_number}{shelf_code}".upper()
                mysim_location_id = mysim_locations.get(code)

                if mysim_location_id is None:
                    missing.append(code)
                    continue

                targets.append(
                    {
                        "code": code,
                        "name": code,
                        "type": "shelf",
                        "aisle_code": aisle_code,
                        "rack_code": str(rack_number),
                        "shelf_code": shelf_code,
                        "mysim_code": code,
                        "mysim_location_id": mysim_location_id,
                    }
                )

    # CN235 1A - CN235 8F -> AISLE1
    add_range(
        prefix="CN235",
        rack_start=1,
        rack_end=8,
        aisle_code="AISLE1",
    )

    # CN235 9A - CN235 11F -> AISLE2
    add_range(
        prefix="CN235",
        rack_start=9,
        rack_end=11,
        aisle_code="AISLE2",
    )

    # C295 1A - C295 3F -> AISLE2
    add_range(
        prefix="C295",
        rack_start=1,
        rack_end=3,
        aisle_code="AISLE2",
    )

    return targets, missing


# ============================================================
# BASE DE DATOS
# ============================================================

def ensure_schema(conn: psycopg.Connection) -> None:
    """
    Crea tablas mínimas si no existen y añade columnas necesarias a locations.

    Si ya existen, no toca lo importante.
    Porque romper producción por una migración alegre es una tradición,
    pero no una buena.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS aisles (
                id BIGSERIAL PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS device_groups (
                id BIGSERIAL PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS aisle_device_groups (
                id BIGSERIAL PRIMARY KEY,
                aisle_id BIGINT NOT NULL REFERENCES aisles(id) ON DELETE CASCADE,
                device_group_id BIGINT NOT NULL REFERENCES device_groups(id) ON DELETE CASCADE,
                is_primary BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_aisle_device_group UNIQUE (aisle_id, device_group_id)
            );
            """
        )

        cur.execute(
            """
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS aisle_id BIGINT;
            """
        )

        cur.execute(
            """
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS rack_code TEXT;
            """
        )

        cur.execute(
            """
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS shelf_code TEXT;
            """
        )

        cur.execute(
            """
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS mysim_location_id BIGINT;
            """
        )

        cur.execute(
            """
            ALTER TABLE locations
            ADD COLUMN IF NOT EXISTS mysim_code TEXT;
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_locations_aisle_id
            ON locations (aisle_id);
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_locations_mysim_location_id
            ON locations (mysim_location_id);
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_aisle_device_groups_aisle_id
            ON aisle_device_groups (aisle_id);
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_aisle_device_groups_device_group_id
            ON aisle_device_groups (device_group_id);
            """
        )


def get_or_create_aisle(conn: psycopg.Connection, code: str, name: str) -> int:
    code = code.strip().upper()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM aisles
            WHERE UPPER(code) = %s
            ORDER BY id
            LIMIT 1;
            """,
            (code,),
        )

        row = cur.fetchone()

        if row is not None:
            aisle_id = int(row[0])

            cur.execute(
                """
                UPDATE aisles
                SET
                    code = %s,
                    name = %s,
                    is_active = TRUE
                WHERE id = %s;
                """,
                (code, name, aisle_id),
            )

            return aisle_id

        cur.execute(
            """
            INSERT INTO aisles (
                code,
                name,
                is_active
            )
            VALUES (%s, %s, TRUE)
            RETURNING id;
            """,
            (code, name),
        )

        return int(cur.fetchone()[0])


def get_or_create_device_group(conn: psycopg.Connection, code: str, name: str) -> int:
    code = code.strip().upper()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM device_groups
            WHERE UPPER(code) = %s
            ORDER BY id
            LIMIT 1;
            """,
            (code,),
        )

        row = cur.fetchone()

        if row is not None:
            device_group_id = int(row[0])

            cur.execute(
                """
                UPDATE device_groups
                SET
                    code = %s,
                    name = %s,
                    is_active = TRUE
                WHERE id = %s;
                """,
                (code, name, device_group_id),
            )

            return device_group_id

        cur.execute(
            """
            INSERT INTO device_groups (
                code,
                name,
                is_active
            )
            VALUES (%s, %s, TRUE)
            RETURNING id;
            """,
            (code, name),
        )

        return int(cur.fetchone()[0])


def ensure_base_data(conn: psycopg.Connection) -> dict[str, int]:
    aisle_ids = {
        "AISLE1": get_or_create_aisle(conn, "AISLE1", "Aisle 1"),
        "AISLE2": get_or_create_aisle(conn, "AISLE2", "Aisle 2"),
    }

    get_or_create_device_group(conn, "CN235", "CN235")
    get_or_create_device_group(conn, "235", "235")
    get_or_create_device_group(conn, "C295", "C295")
    get_or_create_device_group(conn, "295", "295")

    return aisle_ids


def get_device_group_id(conn: psycopg.Connection, code: str) -> int:
    code = code.strip().upper()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM device_groups
            WHERE UPPER(code) = %s
            ORDER BY id
            LIMIT 1;
            """,
            (code,),
        )

        row = cur.fetchone()

    if row is None:
        raise RuntimeError(f"No existe device_group con code={code}")

    return int(row[0])


def link_aisle_to_device_groups(
    conn: psycopg.Connection,
    *,
    aisle_id: int,
    device_group_codes: list[str],
) -> None:
    with conn.cursor() as cur:
        for group_code in device_group_codes:
            device_group_id = get_device_group_id(conn, group_code)

            cur.execute(
                """
                INSERT INTO aisle_device_groups (
                    aisle_id,
                    device_group_id,
                    is_primary,
                    is_active
                )
                VALUES (%s, %s, FALSE, TRUE)
                ON CONFLICT (aisle_id, device_group_id)
                DO UPDATE SET
                    is_active = TRUE;
                """,
                (aisle_id, device_group_id),
            )


def ensure_aisle_device_groups(
    conn: psycopg.Connection,
    aisle_ids: dict[str, int],
) -> None:
    # AISLE1 acepta CN235 y 235
    link_aisle_to_device_groups(
        conn,
        aisle_id=aisle_ids["AISLE1"],
        device_group_codes=["CN235", "235"],
    )

    # AISLE2 acepta CN235, 235, C295 y 295
    link_aisle_to_device_groups(
        conn,
        aisle_id=aisle_ids["AISLE2"],
        device_group_codes=["CN235", "235", "C295", "295"],
    )


def find_location_id_by_code(conn: psycopg.Connection, code: str) -> int | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id
            FROM locations
            WHERE UPPER(code) = %s
            ORDER BY id
            LIMIT 1;
            """,
            (code.upper(),),
        )

        row = cur.fetchone()

    if row is None:
        return None

    return int(row[0])


def upsert_location(
    conn: psycopg.Connection,
    *,
    target: dict,
    aisle_ids: dict[str, int],
) -> int:
    code = target["code"].strip().upper()
    aisle_id = aisle_ids[target["aisle_code"]]

    existing_id = find_location_id_by_code(conn, code)

    with conn.cursor() as cur:
        if existing_id is not None:
            cur.execute(
                """
                UPDATE locations
                SET
                    code = %(code)s,
                    name = %(name)s,
                    type = %(type)s,
                    aisle_id = %(aisle_id)s,
                    rack_code = %(rack_code)s,
                    shelf_code = %(shelf_code)s,
                    mysim_location_id = %(mysim_location_id)s,
                    mysim_code = %(mysim_code)s,
                    is_active = TRUE
                WHERE id = %(id)s;
                """,
                {
                    "id": existing_id,
                    "code": code,
                    "name": target["name"],
                    "type": target["type"],
                    "aisle_id": aisle_id,
                    "rack_code": target["rack_code"],
                    "shelf_code": target["shelf_code"],
                    "mysim_location_id": target["mysim_location_id"],
                    "mysim_code": target["mysim_code"],
                },
            )

            return existing_id

        cur.execute(
            """
            INSERT INTO locations (
                code,
                name,
                type,
                aisle_id,
                rack_code,
                shelf_code,
                mysim_location_id,
                mysim_code,
                is_active
            )
            VALUES (
                %(code)s,
                %(name)s,
                %(type)s,
                %(aisle_id)s,
                %(rack_code)s,
                %(shelf_code)s,
                %(mysim_location_id)s,
                %(mysim_code)s,
                TRUE
            )
            RETURNING id;
            """,
            {
                "code": code,
                "name": target["name"],
                "type": target["type"],
                "aisle_id": aisle_id,
                "rack_code": target["rack_code"],
                "shelf_code": target["shelf_code"],
                "mysim_location_id": target["mysim_location_id"],
                "mysim_code": target["mysim_code"],
            },
        )

        return int(cur.fetchone()[0])


def import_locations(
    conn: psycopg.Connection,
    *,
    targets: list[dict],
    aisle_ids: dict[str, int],
) -> None:
    for target in targets:
        upsert_location(
            conn,
            target=target,
            aisle_ids=aisle_ids,
        )


# ============================================================
# RESUMEN
# ============================================================

def print_summary(targets: list[dict], missing: list[str]) -> None:
    print(f"Localizaciones objetivo encontradas en JSON: {len(targets)}")
    print(f"Localizaciones objetivo no encontradas en JSON: {len(missing)}")

    by_aisle: dict[str, int] = {}

    for target in targets:
        aisle_code = target["aisle_code"]
        by_aisle[aisle_code] = by_aisle.get(aisle_code, 0) + 1

    print("\nResumen por pasillo:")

    for aisle_code, total in sorted(by_aisle.items()):
        print(f"  {aisle_code}: {total}")

    if missing:
        print("\nFaltan estas localizaciones en el JSON:")

        for code in missing:
            print(f"  {code}")


def print_preview(targets: list[dict], limit: int = 20) -> None:
    print("\nPrimeras localizaciones que se importarían:")

    for target in targets[:limit]:
        print(
            f"  {target['code']} -> "
            f"aisle={target['aisle_code']}, "
            f"rack={target['rack_code']}, "
            f"shelf={target['shelf_code']}, "
            f"mysim_id={target['mysim_location_id']}"
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    mysim_locations = load_mysim_locations(INPUT_FILE)
    targets, missing = build_target_locations(mysim_locations)

    print_summary(targets, missing)
    print_preview(targets)

    if DRY_RUN:
        print("\nDRY_RUN=True")
        print("No se ha tocado la base de datos.")
        print("Cuando esté revisado, cambia DRY_RUN = False y vuelve a ejecutar.")
        return

    with psycopg.connect(DATABASE_URL) as conn:
        ensure_schema(conn)

        aisle_ids = ensure_base_data(conn)

        ensure_aisle_device_groups(
            conn,
            aisle_ids=aisle_ids,
        )

        import_locations(
            conn,
            targets=targets,
            aisle_ids=aisle_ids,
        )

        conn.commit()

    print("\nImportación completada correctamente.")
    print("Se han actualizado locations y aisle_device_groups.")


if __name__ == "__main__":
    main()