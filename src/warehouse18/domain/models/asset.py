from sqlalchemy import Column, BigInteger, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from .base import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(BigInteger, primary_key=True)
    asset_code = Column(Text, nullable=False, unique=True)
    item_id = Column(BigInteger, ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    status = Column(Text, nullable=False, server_default="active")  # active/repair/scrapped/lost/inactive
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    location = relationship("AssetLocation", uselist=False, back_populates="asset")