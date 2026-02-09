from sqlalchemy import Column, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from .base import Base

class AssetLocation(Base):
    __tablename__ = "asset_location"

    asset_id = Column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True)
    location_id = Column(BigInteger, ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    since = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    asset = relationship("Asset", back_populates="location")
