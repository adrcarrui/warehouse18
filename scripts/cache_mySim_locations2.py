from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from warehouse18.infrastructure.integrations.mySim.client import (
    MySimClient,
    MySimConfig,
    rows_normalized,
)

OUTPUT_DIR = Path("scripts/_cache")
OUTPUT_JSON = OUTPUT_DIR / "mysim_locations_code_to_id.json"
OUTPUT_DUPES = OUTPUT_DIR / "mysim_locations_duplicates.json"
OUTPUT_RAW = OUTPUT_DIR / "mysim_locations_raw.json"


def _norm_code(code: str) -> str:
    # Normalización para evitar duplicados por mayúsculas/espacios
    return " ".join(code.strip().split()).casefold()


def main() -> int:
    load_dotenv()

    cfg = MySimConfig.from_env()
    cfg = replace(cfg, timeout=90)

    client = MySimClient(cfg)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"TOKEN present: {bool(cfg.token)} len: {len(cfg.token) if cfg.token else 0}")
    print(f"Base URL: {cfg.base_url}")
    print(f"Timeout: {cfg.timeout}")

    try:
        resp = client.get(entity="location", limit=5000)
    except Exception as e:
        print(f"ERROR llamando a mySim: {e}")
        return 1

    # Guardar RAW siempre, para inspección
    OUTPUT_RAW.write_text(
        json.dumps(resp, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"RAW guardado en: {OUTPUT_RAW}")

    print(type(resp))
    print(json.dumps(resp, ensure_ascii=False, indent=2)[:8000])

    rows = rows_normalized(resp)

    print("Locations recibidas:", len(rows))
    if not rows:
        print("⚠️ No hay rows normalizadas.")
        return 2

    # ------------------------------------------------------------
    # BÚSQUEDA DIRECTA DE LA LOCALIZACIÓN NUEVA
    # ------------------------------------------------------------
    target_code = "W18-AISLE1"
    target_id = 2790

    found = [
        r
        for r in rows
        if str(r.get("locationCode", "")).strip().upper() == target_code.upper()
        or r.get("id") == target_id
        or str(target_code).upper() in json.dumps(r, ensure_ascii=False).upper()
        or str(target_id) in json.dumps(r, ensure_ascii=False)
    ]

    print("\n=== BÚSQUEDA DIRECTA ===")
    print(f"Buscando locationCode={target_code!r} o id={target_id}")
    print("Encontradas:", len(found))
    for i, r in enumerate(found, start=1):
        print(f"\n--- MATCH {i} ---")
        print(json.dumps(r, ensure_ascii=False, indent=2))

    # También mirar si está en el RAW completo
    raw_dump = json.dumps(resp, ensure_ascii=False)
    print("\n=== PRESENCIA EN RAW ===")
    print(f"{target_code!r} en RAW:", target_code in raw_dump)
    print(f"{target_id!r} en RAW:", str(target_id) in raw_dump)

    # ------------------------------------------------------------
    # CONSTRUIR MAPA NORMALIZADO
    # ------------------------------------------------------------
    code_to_id: Dict[str, int] = {}
    duplicates: List[Dict[str, Any]] = []

    skipped_missing = 0
    skipped_bad_id = 0

    for r in rows:
        code = r.get("locationCode")
        raw_id = r.get("id")

        if code in (None, "") or raw_id in (None, ""):
            skipped_missing += 1
            print("DESCARTADA por campos faltantes:")
            print(json.dumps(r, ensure_ascii=False, indent=2))
            continue

        try:
            loc_id = int(raw_id)
        except Exception:
            skipped_bad_id += 1
            print("DESCARTADA por id no numérico:")
            print(json.dumps(r, ensure_ascii=False, indent=2))
            continue

        key = _norm_code(str(code))
        if not key:
            skipped_missing += 1
            print("DESCARTADA por key vacía tras normalización:")
            print(json.dumps(r, ensure_ascii=False, indent=2))
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
            continue

        code_to_id[key] = loc_id

    OUTPUT_JSON.write_text(
        json.dumps(code_to_id, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    OUTPUT_DUPES.write_text(
        json.dumps(duplicates, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n=== RESUMEN ===")
    print("Únicas guardadas:", len(code_to_id))
    print("Duplicados detectados:", len(duplicates))
    print("Filas saltadas (faltan campos):", skipped_missing)
    print("Filas saltadas (id no numérico):", skipped_bad_id)
    print("OK ->", OUTPUT_JSON)
    print("DUPE LOG ->", OUTPUT_DUPES)

    # Comprobación directa en el JSON final
    normalized_target = _norm_code(target_code)
    print("\n=== COMPROBACIÓN EN MAPA FINAL ===")
    if normalized_target in code_to_id:
        print(
            f"{target_code!r} SÍ está en el mapa final con id={code_to_id[normalized_target]}"
        )
    else:
        print(f"{target_code!r} NO está en el mapa final")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())