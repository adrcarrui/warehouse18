from sqlalchemy import Column, BigInteger, ForeignKey, Integer, Text, DateTime, text
from sqlalchemy.orm import relationship

from .base import Base


class AssetEnrichment(Base):
    __tablename__ = "asset_enrichment"

    asset_id = Column(
        BigInteger,
        ForeignKey("assets.id", ondelete="CASCADE"),
        primary_key=True,
    )

    serial_number = Column(Text, nullable=True)

    sync_status = Column(
        Text,
        nullable=False,
        server_default=text("'pending'"),
    )

    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    retries = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    asset = relationship("Asset")