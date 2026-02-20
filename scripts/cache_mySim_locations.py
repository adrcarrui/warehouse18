from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from warehouse18.infrastructure.integrations.mySim.client import MySimClient, MySimConfig, rows_normalized

OUTPUT_DIR = Path("scripts/_cache")
OUTPUT_JSON = OUTPUT_DIR / "mysim_locations_code_to_id.json"
OUTPUT_DUPES = OUTPUT_DIR / "mysim_locations_duplicates.json"


def _norm_code(code: str) -> str:
    # Normalización para evitar duplicados por mayúsculas/espacios
    return " ".join(code.strip().split()).casefold()


def main() -> int:
    load_dotenv()

    cfg = MySimConfig.from_env()
    client = MySimClient(cfg)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    resp = client.get(entity="location", limit=5)
    rows = rows_normalized(resp)

    print("Locations recibidas:", len(rows))
    if not rows:
        # guardamos raw por si acaso
        raw_path = OUTPUT_DIR / "mysim_locations_raw.json"
        raw_path.write_text(json.dumps(resp, ensure_ascii=False, indent=2), encoding="utf-8")
        print("⚠️ No hay rows. Guardé RAW en:", raw_path)
        return 2

    code_to_id: Dict[str, int] = {}
    duplicates: List[Dict[str, Any]] = []

    skipped_missing = 0
    skipped_bad_id = 0

    for r in rows:
        code = r.get("locationCode")
        raw_id = r.get("id")

        if code in (None, "") or raw_id in (None, ""):
            skipped_missing += 1
            continue

        try:
            loc_id = int(raw_id)
        except Exception:
            skipped_bad_id += 1
            continue

        key = _norm_code(str(code))
        if not key:
            skipped_missing += 1
            continue

        if key in code_to_id and code_to_id[key] != loc_id:
            duplicates.append(
                {
                    "locationCode_normalized": key,
                    "existing_id": code_to_id[key],
                    "new_id": loc_id,
                    "raw_row": r,
                }
            )
            # no sobreescribimos
            continue

        code_to_id[key] = loc_id

    #OUTPUT_JSON.write_text(json.dumps(code_to_id, ensure_ascii=False, indent=2), encoding="utf-8")
    #OUTPUT_DUPES.write_text(json.dumps(duplicates, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Únicas guardadas:", len(code_to_id))
    print("Duplicados detectados:", len(duplicates))
    print("Filas saltadas (faltan campos):", skipped_missing)
    print("Filas saltadas (id no numérico):", skipped_bad_id)
    print("OK ->", OUTPUT_JSON)
    print("DUPE LOG ->", OUTPUT_DUPES)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
