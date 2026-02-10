# src/warehouse18_api/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from typing import Generic, List, TypeVar

class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

class UserCreateIn(BaseModel):
    username: str = Field(min_length=1)
    full_name: str = Field(min_length=1)          # NOT NULL en DB
    email: Optional[str] = None
    role: str = Field(min_length=1)
    department: Optional[str] = None
    is_active: bool = True
    password_hash: Optional[str] = None           # nullable en DB
    auth_provider: str = "local"

class UserOut(ORMBase):
    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    role: str
    department: Optional[str] = None
    is_active: bool
    auth_provider: str
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class UserUpdateIn(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1)
    email: Optional[str] = None
    role: Optional[str] = Field(default=None, min_length=1)
    department: Optional[str] = None
    is_active: Optional[bool] = None
    password_hash: Optional[str] = None
    auth_provider: Optional[str] = None

class LocationCreateIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=50)
    parent_id: Optional[int] = None
    is_active: bool = True


class LocationUpdateIn(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None


class LocationOut(ORMBase):
    id: int
    code: str
    name: str
    type: str
    parent_id: Optional[int] = None
    is_active: bool

class ItemCreateIn(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    category: Optional[str] = None
    uom: str = Field(min_length=1)
    is_serialized: bool = False
    min_stock: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    is_active: bool = True
    item_code: Optional[str] = None


class ItemUpdateIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    uom: Optional[str] = None
    is_serialized: Optional[bool] = None
    min_stock: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    is_active: Optional[bool] = None
    item_code: Optional[str] = None


class ItemOut(ORMBase):
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    uom: str
    is_serialized: bool
    min_stock: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    is_active: bool
    item_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AssetCreateIn(BaseModel):
    asset_code: str = Field(min_length=1)
    item_id: Optional[int] = None
    status: str = "active"
    # opcional: poner ubicación inicial
    location_id: Optional[int] = None

class AssetUpdateIn(BaseModel):
    item_id: Optional[int] = None
    status: Optional[str] = None
    # opcional: cambiar ubicación actual (si quieres sin usar SP)
    location_id: Optional[int] = None

class AssetOut(ORMBase):
    id: int
    asset_code: str
    item_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    location_id: Optional[int] = None
    location_since: Optional[datetime] = None

class StockContainerCreateIn(BaseModel):
    container_code: str = Field(min_length=1)
    item_id: int
    location_id: int
    quantity: Decimal = Field(ge=0)
    status: str = "open"
    is_active: bool = True

class StockContainerUpdateIn(BaseModel):
    container_code: Optional[str] = None
    item_id: Optional[int] = None
    location_id: Optional[int] = None
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    status: Optional[str] = None
    is_active: Optional[bool] = None

class StockContainerOut(ORMBase):
    id: int
    container_code: str
    item_id: int
    location_id: int
    quantity: Decimal
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class InventoryStockOut(ORMBase):
    id: int
    item_id: int
    location_id: int
    quantity: Decimal
    updated_at: datetime

class MovementTypeOut(BaseModel):
    id: int
    code: str
    name: str
    affects_stock: bool
    affects_location: bool
    stock_sign: int

class MovementCreateIn(BaseModel):
    movement_type_id: int

    item_id: Optional[int] = None
    quantity: Optional[Decimal] = Field(default=None, ge=0)

    from_location_id: Optional[int] = None
    to_location_id: Optional[int] = None

    reference_type: Optional[str] = None  # 'asset' | 'container'
    reference_id: Optional[int] = None

    user_id: Optional[int] = None
    notes: Optional[str] = None


class MovementOut(ORMBase):
    id: int
    movement_type_id: int

    item_id: Optional[int] = None
    quantity: Optional[Decimal] = None

    from_location_id: Optional[int] = None
    to_location_id: Optional[int] = None

    reference_type: Optional[str] = None
    reference_id: Optional[int] = None

    user_id: Optional[int] = None
    created_at: datetime
    notes: Optional[str] = None

T = TypeVar("T")

class PageOut(BaseModel, Generic[T]):
    items: List[T]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)