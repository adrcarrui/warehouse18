from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from warehouse18.infrastructure.db import SessionLocal
from warehouse18.infrastructure.integrations.mySim.client import (
    MySimClient,
    MySimConfig,
    rows_normalized,
)


def _norm(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def _pick_display_name(row: dict[str, Any], code: str) -> str:
    description = row.get("description")
    if description is not None:
        description_text = str(description).strip()
        if description_text:
            return description_text

    return code


def main() -> int:
    load_dotenv()

    cfg = replace(MySimConfig.from_env(), timeout=90)
    client = MySimClient(cfg)

    print(f"TOKEN present: {bool(cfg.token)} len: {len(cfg.token) if cfg.token else 0}")
    print(f"Base URL: {cfg.base_url}")
    print(f"Timeout: {cfg.timeout}")

    try:
        resp = client.get(entity="location", limit=5000)
    except Exception as e:
        print(f"ERROR llamando a mySim: {e}")
        return 1

    rows = rows_normalized(resp)
    print("Locations recibidas:", len(rows))

    if not rows:
        print("No hay rows normalizadas.")
        return 2

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        raw_id = row.get("id")
        raw_code = row.get("locationCode")

        if raw_id in (None, "") or raw_code in (None, ""):
            continue

        external_id = str(raw_id).strip()
        code = str(raw_code).strip()

        if not external_id or not code:
            continue

        grouped[_norm(code)].append(
            {
                "external_id": external_id,
                "code": code,
                "display_name": _pick_display_name(row, code),
                "description": row.get("description"),
                "raw": row,
            }
        )

    print("Grupos únicos por code:", len(grouped))

    db: Session = SessionLocal()
    inserted_groups = 0
    updated_groups = 0
    inserted_ids = 0
    updated_ids = 0

    try:
        now = datetime.now(timezone.utc)

        for normalized_code, entries in grouped.items():
            entries_sorted = sorted(entries, key=lambda x: x["external_id"])
            canonical_code = entries_sorted[0]["code"]
            display_name = entries_sorted[0]["display_name"]
            description = entries_sorted[0]["description"]

            # 1. Upsert grupo
            group_row = db.execute(
                text(
                    """
                    SELECT id, code, display_name, description
                    FROM public.mysim_location_groups
                    WHERE normalized_code = :normalized_code
                    """
                ),
                {"normalized_code": normalized_code},
            ).mappings().first()

            if group_row is None:
                result = db.execute(
                    text(
                        """
                        INSERT INTO public.mysim_location_groups
                            (code, normalized_code, display_name, description, created_at, updated_at)
                        VALUES
                            (:code, :normalized_code, :display_name, :description, :created_at, :updated_at)
                        RETURNING id
                        """
                    ),
                    {
                        "code": canonical_code,
                        "normalized_code": normalized_code,
                        "display_name": display_name,
                        "description": description,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
                group_id = result.scalar_one()
                inserted_groups += 1
            else:
                group_id = group_row["id"]

                changed = (
                    group_row["code"] != canonical_code
                    or group_row["display_name"] != display_name
                    or group_row["description"] != description
                )

                if changed:
                    db.execute(
                        text(
                            """
                            UPDATE public.mysim_location_groups
                            SET
                                code = :code,
                                display_name = :display_name,
                                description = :description,
                                updated_at = :updated_at
                            WHERE id = :id
                            """
                        ),
                        {
                            "id": group_id,
                            "code": canonical_code,
                            "display_name": display_name,
                            "description": description,
                            "updated_at": now,
                        },
                    )
                    updated_groups += 1

            # 2. Upsert ids externos del grupo
            for entry in entries_sorted:
                existing_id_row = db.execute(
                    text(
                        """
                        SELECT id, mysim_location_group_id
                        FROM public.mysim_location_group_ids
                        WHERE external_id = :external_id
                        """
                    ),
                    {"external_id": entry["external_id"]},
                ).mappings().first()

                if existing_id_row is None:
                    db.execute(
                        text(
                            """
                            INSERT INTO public.mysim_location_group_ids
                                (mysim_location_group_id, external_id, raw_json, created_at)
                            VALUES
                                (:group_id, :external_id, CAST(:raw_json AS jsonb), :created_at)
                            """
                        ),
                        {
                            "group_id": group_id,
                            "external_id": entry["external_id"],
                            "raw_json": __import__("json").dumps(entry["raw"], ensure_ascii=False),
                            "created_at": now,
                        },
                    )
                    inserted_ids += 1
                else:
                    if existing_id_row["mysim_location_group_id"] != group_id:
                        db.execute(
                            text(
                                """
                                UPDATE public.mysim_location_group_ids
                                SET
                                    mysim_location_group_id = :group_id,
                                    raw_json = CAST(:raw_json AS jsonb)
                                WHERE id = :id
                                """
                            ),
                            {
                                "id": existing_id_row["id"],
                                "group_id": group_id,
                                "raw_json": __import__("json").dumps(entry["raw"], ensure_ascii=False),
                            },
                        )
                        updated_ids += 1
                    else:
                        db.execute(
                            text(
                                """
                                UPDATE public.mysim_location_group_ids
                                SET raw_json = CAST(:raw_json AS jsonb)
                                WHERE id = :id
                                """
                            ),
                            {
                                "id": existing_id_row["id"],
                                "raw_json": __import__("json").dumps(entry["raw"], ensure_ascii=False),
                            },
                        )

        db.commit()

        print("\n=== RESUMEN ===")
        print("Inserted groups:", inserted_groups)
        print("Updated groups:", updated_groups)
        print("Inserted ids:", inserted_ids)
        print("Updated ids:", updated_ids)

        return 0

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())