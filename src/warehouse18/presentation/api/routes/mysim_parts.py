from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter
from warehouse18.presentation.api.desp import get_mysim_gateway

router = APIRouter(prefix="/mysim/parts", tags=["mysim"])


@router.get("/{part_db_id}")
def get_mysim_part(
    part_db_id: int,
    mysim: MySimAdapter = Depends(get_mysim_gateway),
) -> dict[str, Any]:
    try:
        part = mysim.get_part_by_id(part_db_id)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Error consulting mySim: {error}",
        ) from error

    if part is None:
        raise HTTPException(
            status_code=404,
            detail=f"Part {part_db_id} not found in mySim",
        )

    part_code = str(part.get("partId") or "").strip().upper()

    if not part_code:
        raise HTTPException(
            status_code=502,
            detail="mySim returned a part without partId",
        )

    family = part_code.split("-", 1)[0]

    return {
        "part_db_id": part_db_id,
        "part_code": part_code,
        "family": family,
        "part": part,
    }