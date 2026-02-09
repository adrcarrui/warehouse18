from sqlalchemy import Column, BigInteger, DateTime, Numeric, ForeignKey, func
from .base import Base

class InventoryStock(Base):
    __tablename__ = "inventory_stock"

    id = Column(BigInteger, primary_key=True)
    item_id = Column(BigInteger, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(BigInteger, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)

    quantity = Column(Numeric(18, 6), nullable=False, server_default="0")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
