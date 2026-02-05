# src/warehouse18_api/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class ReceiveContainerIn(BaseModel):
    container_code: str
    item_id: int
    location_code: str
    qty: float = Field(gt=0)
    user_id: Optional[int] = None
    notes: Optional[str] = None

class ConsumeContainerIn(BaseModel):
    container_code: str
    qty: float = Field(gt=0)
    user_id: Optional[int] = None
    notes: Optional[str] = None

class TransferContainerIn(BaseModel):
    container_code: str
    to_location_code: str
    user_id: Optional[int] = None
    notes: Optional[str] = None

class ReceiveAssetIn(BaseModel):
    asset_code: str
    item_id: int
    to_location_code: str
    user_id: Optional[int] = None
    notes: Optional[str] = None
    create_enrichment: bool = True

class TransferAssetIn(BaseModel):
    asset_code: str
    to_location_code: str
    user_id: Optional[int] = None
    notes: Optional[str] = None

class IssueAssetIn(BaseModel):
    asset_code: str
    user_id: Optional[int] = None
    notes: Optional[str] = None
    new_status: str = "inactive"

class OkOut(BaseModel):
    ok: bool = True
    movement_id: int
