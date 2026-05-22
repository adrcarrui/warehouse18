from sqlalchemy import Column, BigInteger, ForeignKey, Numeric, text
from sqlalchemy.orm import relationship

from .base import Base


class MovementAsset(Base):
    __tablename__ = "movement_assets"

    movement_id = Column(
        BigInteger,
        ForeignKey("movements.id", ondelete="CASCADE"),
        primary_key=True,
    )

    asset_id = Column(
        BigInteger,
        ForeignKey("assets.id", ondelete="CASCADE"),
        primary_key=True,
    )

    quantity = Column(
        Numeric(18, 6),
        nullable=False,
        server_default=text("1"),
    )

    movement = relationship("Movement")
    asset = relationship("Asset")