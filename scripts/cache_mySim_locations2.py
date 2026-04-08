from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from warehouse18.infrastructure.integrations.mySim.client import (
    MySimClient,
    MySimConfig,
    rows_normalized,
)

OUTPUT_DIR = Path("scripts/_cache")
OUTPUT_BY_CODE = OUTPUT_DIR / "mysim_locations_by_code.json"
OUTPUT_BY_ID = OUTPUT_DIR / "mysim_locations_by_id.json"
OUTPUT_RAW = OUTPUT_DIR / "mysim_locations_raw.json"
OUTPUT_ISSUES = OUTPUT_DIR / "mysim_locations_issues.json"


def _norm_code(code: str) -> str:
    return " ".join(code.strip().split()).casefold()


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _pick_display_name(row: dict[str, Any], location_code: str, location_id: int) -> str:
    """
    Solo usamos campos reales/razonables:
    - description, si existe y tiene contenido
    - locationCode
    - id
    """
    description = row.get("description")
    if description is not None:
        description_text = str(description).strip()
        if description_text:
            return description_text

    if location_code.strip():
        return location_code.strip()

    return str(location_id)


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

    OUTPUT_RAW.write_text(
        json.dumps(resp, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"RAW guardado en: {OUTPUT_RAW}")

    rows = rows_normalized(resp)
    print("Locations recibidas:", len(rows))

    if not rows:
        print("No hay rows normalizadas.")
        return 2

    print("\n=== EJEMPLO DE ROW REAL ===")
    print(json.dumps(rows[0], ensure_ascii=False, indent=2))

    grouped_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_id: dict[str, dict[str, Any]] = {}
    issues: list[dict[str, Any]] = []

    for row in rows:
        raw_id = row.get("id")
        location_id = _safe_int(raw_id)
        location_code_raw = row.get("locationCode")

        if location_id is None:
            issues.append(
                {
                    "issue": "invalid_or_missing_id",
                    "row": row,
                }
            )
            continue

        if location_code_raw in (None, ""):
            issues.append(
                {
                    "issue": "missing_locationCode",
                    "id": location_id,
                    "row": row,
                }
            )
            continue

        location_code = str(location_code_raw).strip()
        if not location_code:
            issues.append(
                {
                    "issue": "blank_locationCode",
                    "id": location_id,
                    "row": row,
                }
            )
            continue

        norm_code = _norm_code(location_code)
        display_name = _pick_display_name(row, location_code, location_id)

        entry = {
            "id": location_id,
            "code": location_code,
            "normalized_code": norm_code,
            "display_name": display_name,
            "description": row.get("description"),
            "raw": row,
        }

        grouped_by_code[norm_code].append(entry)

        by_id[str(location_id)] = {
            "id": location_id,
            "code": location_code,
            "normalized_code": norm_code,
            "display_name": display_name,
            "description": row.get("description"),
        }

    by_code_output: dict[str, Any] = {}

    for norm_code, entries in grouped_by_code.items():
        entries_sorted = sorted(entries, key=lambda x: x["id"])
        canonical_code = entries_sorted[0]["code"]

        display_names: list[str] = []
        for e in entries_sorted:
            name = str(e["display_name"]).strip()
            if name and name not in display_names:
                display_names.append(name)

        by_code_output[norm_code] = {
            "code": canonical_code,
            "normalized_code": norm_code,
            "display_name": display_names[0] if display_names else canonical_code,
            "ids": [e["id"] for e in entries_sorted],
            "duplicate_count": len(entries_sorted),
            "has_duplicates": len(entries_sorted) > 1,
            "rows": [
                {
                    "id": e["id"],
                    "code": e["code"],
                    "display_name": e["display_name"],
                    "description": e["description"],
                    "raw": e["raw"],
                }
                for e in entries_sorted
            ],
        }

    OUTPUT_BY_CODE.write_text(
        json.dumps(by_code_output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    OUTPUT_BY_ID.write_text(
        json.dumps(by_id, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    OUTPUT_ISSUES.write_text(
        json.dumps(issues, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total_codes = len(by_code_output)
    duplicated_codes = sum(1 for v in by_code_output.values() if v["has_duplicates"])

    print("\n=== RESUMEN ===")
    print("Códigos únicos guardados:", total_codes)
    print("Códigos con duplicados:", duplicated_codes)
    print("Issues:", len(issues))
    print("BY CODE ->", OUTPUT_BY_CODE)
    print("BY ID ->", OUTPUT_BY_ID)
    print("ISSUES ->", OUTPUT_ISSUES)

    target_code = "5F"
    target_norm = _norm_code(target_code)
    print(f"\n=== COMPROBACIÓN {target_code!r} ===")
    if target_norm in by_code_output:
        print(json.dumps(by_code_output[target_norm], ensure_ascii=False, indent=2))
    else:
        print(f"{target_code!r} no encontrado")

    target_id = "1862"
    print(f"\n=== COMPROBACIÓN ID {target_id} ===")
    if target_id in by_id:
        print(json.dumps(by_id[target_id], ensure_ascii=False, indent=2))
    else:
        print(f"id={target_id} no encontrado")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())