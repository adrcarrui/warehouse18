from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite ejecutar el script aunque no tengas instalado el paquete en editable.
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from warehouse18.application.movements.confirm_serialized_asset import (  # noqa: E402
    ConfirmSerializedAssetError,
    confirm_serialized_asset_movement,
)
from warehouse18.infrastructure.db import SessionLocal  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test manual para confirmar un movimiento como asset serializado."
    )

    parser.add_argument(
        "movement_id",
        type=int,
        help="ID del movimiento a confirmar.",
    )

    parser.add_argument(
        "--asset-code",
        default=None,
        help="EPC / asset_code. Si no se pasa, se intenta leer desde movement.notes con epc=...",
    )

    parser.add_argument(
        "--item-code",
        default=None,
        help="PART ID / item_code. Si no se pasa, se usa movement.item_key.",
    )

    parser.add_argument(
        "--commit",
        action="store_true",
        help="Guarda los cambios. Si no se usa, hace rollback.",
    )

    parser.add_argument(
        "--no-enrichment",
        action="store_true",
        help="No crea asset_enrichment.",
    )

    parser.add_argument(
        "--no-outbox",
        action="store_true",
        help="No crea integration_outbox.",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        result = confirm_serialized_asset_movement(
            db,
            movement_id=args.movement_id,
            asset_code=args.asset_code,
            item_code=args.item_code,
            create_enrichment=not args.no_enrichment,
            enqueue_sync=not args.no_outbox,
        )

        print("OK: movimiento serializado procesado")
        print(f"  movement_id:        {result.movement_id}")
        print(f"  movement_type_code: {result.movement_type_code}")
        print(f"  item_id:            {result.item_id}")
        print(f"  item_code:          {result.item_code}")
        print(f"  asset_id:           {result.asset_id}")
        print(f"  asset_code:         {result.asset_code}")

        if args.commit:
            db.commit()
            print("COMMIT realizado")
        else:
            db.rollback()
            print("ROLLBACK realizado. No se han guardado cambios.")

        return 0

    except ConfirmSerializedAssetError as exc:
        db.rollback()
        print(f"ERROR CONTROLADO: {exc}")
        return 2

    except Exception as exc:
        db.rollback()
        print(f"ERROR NO CONTROLADO: {type(exc).__name__}: {exc}")
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())