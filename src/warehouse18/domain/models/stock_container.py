from sqlalchemy import Column, BigInteger, Text, Boolean, DateTime, Numeric, ForeignKey, func
from .base import Base

class StockContainer(Base):
    __tablename__ = "stock_containers"

    id = Column(BigInteger, primary_key=True)
    container_code = Column(Text, nullable=True, unique=True)  # nullable según tu DB
    item_id = Column(BigInteger, ForeignKey("items.id", ondelete="RESTRICT"), nullable=False)
    location_id = Column(BigInteger, ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)

    quantity = Column(Numeric(18, 6), nullable=False)
    status = Column(Text, nullable=False, server_default="available")  # ajusta si tu CHECK define otros

    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
