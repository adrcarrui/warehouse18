from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter(prefix="/rfid", tags=["rfid"])


@router.get("/epc-schema")
def get_epc_schema():
    root = Path(__file__).resolve().parents[5]
    schema_path = root / "config" / "epc_schema.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)