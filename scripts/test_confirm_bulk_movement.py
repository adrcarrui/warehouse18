from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from warehouse18.application.movements.confirm_bulk_movement import (  # noqa: E402
    ConfirmBulkMovementError,
    confirm_bulk_movement,
)
from warehouse18.infrastructure.db import SessionLocal  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test manual para confirmar un movimiento no serializado / bulk."
    )

    parser.add_argument(
        "movement_id",
        type=int,
        help="ID del movimiento a confirmar.",
    )

    parser.add_argument(
        "--container-code",
        default=None,
        help="Código EPC/tag del contenedor. Si no se pasa, usa movement.detected_asset_code o notes epc=...",
    )

    parser.add_argument(
        "--item-code",
        default=None,
        help="Código del item. Si no se pasa, usa movement.item_key.",
    )

    parser.add_argument(
        "--commit",
        action="store_true",
        help="Guarda los cambios. Si no se usa, hace rollback.",
    )

    parser.add_argument(
        "--no-outbox",
        action="store_true",
        help="No crea evento en integration_outbox.",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        result = confirm_bulk_movement(
            db,
            movement_id=args.movement_id,
            container_code=args.container_code,
            item_code=args.item_code,
            enqueue_sync=not args.no_outbox,
        )

        print("OK: movimiento bulk procesado")
        print(f"  movement_id:        {result.movement_id}")
        print(f"  movement_type_code: {result.movement_type_code}")
        print(f"  item_id:            {result.item_id}")
        print(f"  item_code:          {result.item_code}")
        print(f"  container_id:       {result.container_id}")
        print(f"  container_code:     {result.container_code}")
        print(f"  quantity:           {result.quantity}")

        if args.commit:
            db.commit()
            print("COMMIT realizado")
        else:
            db.rollback()
            print("ROLLBACK realizado. No se han guardado cambios.")

        return 0

    except ConfirmBulkMovementError as exc:
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