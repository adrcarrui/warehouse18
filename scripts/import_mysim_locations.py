from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
load_dotenv()

def load_json(json_path: Path) -> dict[str, int]:
    if not json_path.exists():
        raise FileNotFoundError(f"No existe el fichero JSON: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("El JSON debe tener formato dict: {nombre: id_mysim}")

    normalized: dict[str, int] = {}
    for raw_name, raw_id in data.items():
        name = str(raw_name).strip()
        if not name:
            continue

        try:
            mysim_id = int(raw_id)
        except (TypeError, ValueError) as e:
            raise ValueError(f"ID no válido para {raw_name!r}: {raw_id!r}") from e

        normalized[name] = mysim_id

    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Importa localizaciones mySim a public.locations sin duplicar por code."
    )
    parser.add_argument(
        "--json",
        default="scripts/_cache/mysim_locations_code_to_id.json",
        help="Ruta al JSON con formato {nombre: id_mysim}",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="Cadena de conexión PostgreSQL. Si no se indica, usa DATABASE_URL del entorno.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No inserta nada, solo muestra lo que haría.",
    )
    args = parser.parse_args()

    if not args.database_url:
        print("ERROR: falta --database-url y no existe DATABASE_URL en el entorno.", file=sys.stderr)
        return 1

    json_path = Path(args.json)
    try:
        locations = load_json(json_path)
    except Exception as e:
        print(f"ERROR cargando JSON: {e}", file=sys.stderr)
        return 1

    print(f"JSON cargado: {json_path}")
    print(f"Localizaciones leídas: {len(locations)}")
    print(f"Modo dry-run: {args.dry_run}")

    inserted = 0
    skipped = 0
    errors = 0

    select_sql = """
        SELECT id, code, name
        FROM public.locations
        WHERE code = %s
    """

    insert_sql = """
        INSERT INTO public.locations (code, name, type, parent_id, is_active)
        VALUES (%s, %s, 'mysim', NULL, TRUE)
        RETURNING id
    """

    try:
        with psycopg.connect(args.database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                for name, mysim_id in locations.items():
                    code = str(mysim_id)

                    try:
                        cur.execute(select_sql, (code,))
                        existing = cur.fetchone()

                        if existing is not None:
                            skipped += 1
                            print(
                                f"[SKIP] code={code} ya existe "
                                f"(id_local={existing['id']}, name={existing['name']!r})"
                            )
                            continue

                        if args.dry_run:
                            inserted += 1
                            print(
                                f"[DRY ] insertaría code={code}, name={name!r}, "
                                f"type='mysim', parent_id=NULL, is_active=TRUE"
                            )
                            continue

                        cur.execute(insert_sql, (code, name))
                        row = cur.fetchone()
                        inserted += 1
                        print(
                            f"[OK  ] insertado code={code}, name={name!r}, id_local={row['id']}"
                        )

                    except Exception as e:
                        errors += 1
                        print(f"[ERR ] code={code}, name={name!r} -> {e}", file=sys.stderr)

                if args.dry_run:
                    conn.rollback()
                else:
                    conn.commit()

    except Exception as e:
        print(f"ERROR conectando o ejecutando en PostgreSQL: {e}", file=sys.stderr)
        return 1

    print("\n=== RESUMEN ===")
    print(f"Insertados: {inserted}")
    print(f"Saltados:   {skipped}")
    print(f"Errores:    {errors}")

    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())