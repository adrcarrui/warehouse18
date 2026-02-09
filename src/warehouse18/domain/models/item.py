from sqlalchemy import Column, BigInteger, Text, Boolean, Numeric, DateTime, func
from .base import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(BigInteger, primary_key=True)

    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    uom = Column(Text, nullable=False)

    is_serialized = Column(Boolean, nullable=False, server_default="false")

    min_stock = Column(Numeric(18, 6), nullable=True)
    reorder_point = Column(Numeric(18, 6), nullable=True)

    is_active = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    item_code = Column(Text, nullable=True, unique=True)
