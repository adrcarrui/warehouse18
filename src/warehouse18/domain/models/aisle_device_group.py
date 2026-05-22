from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship

from .base import Base


class AisleDeviceGroup(Base):
    __tablename__ = "aisle_device_groups"

    id = Column(BigInteger, primary_key=True)

    aisle_id = Column(
        BigInteger,
        ForeignKey("aisles.id", ondelete="CASCADE"),
        nullable=False,
    )

    device_group_id = Column(
        BigInteger,
        ForeignKey("device_groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_primary = Column(Boolean, nullable=False, server_default="false")
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    aisle = relationship("Aisle", back_populates="allowed_device_groups")
    device_group = relationship("DeviceGroup", back_populates="aisle_links")

    __table_args__ = (
        UniqueConstraint(
            "aisle_id",
            "device_group_id",
            name="uq_aisle_device_group",
        ),
    )