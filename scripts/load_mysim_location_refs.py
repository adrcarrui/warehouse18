from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from dotenv import load_dotenv

from warehouse18.infrastructure.integrations.mySim.client import (
    MySimClient,
    MySimConfig,
    rows_normalized,
)


def _norm(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def main() -> int:
    load_dotenv()

    cfg = replace(MySimConfig.from_env(), timeout=90)
    client = MySimClient(cfg)

    resp = client.get(entity="location", limit=5000)
    rows = rows_normalized(resp)

    grouped = defaultdict(list)

    for row in rows:
        code = row.get("locationCode")
        loc_id = row.get("id")

        if code in (None, "") or loc_id in (None, ""):
            continue

        grouped[_norm(str(code))].append(
            {
                "id": str(loc_id).strip(),
                "code": str(code).strip(),
                "description": row.get("description"),
            }
        )

    print("=== PRIMEROS 20 GRUPOS MYSIM ===")
    for i, (norm_code, entries) in enumerate(sorted(grouped.items())[:20], start=1):
        print(f"\n--- GRUPO {i} ---")
        print("normalized:", norm_code)
        print("code:", entries[0]["code"])
        print("ids:", [e["id"] for e in entries])
        print("description:", entries[0]["description"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())