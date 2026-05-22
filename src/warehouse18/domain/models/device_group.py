from sqlalchemy import Column, BigInteger, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class DeviceGroup(Base):
    __tablename__ = "device_groups"

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")

    aliases = relationship("DeviceAlias", back_populates="device_group")

    locations = relationship(
            "Location",
            back_populates="device_group",
        )

    aisle_links = relationship(
        "AisleDeviceGroup",
        back_populates="device_group",
        cascade="all, delete-orphan",
    )


class DeviceAlias(Base):
    __tablename__ = "device_aliases"

    id = Column(BigInteger, primary_key=True)
    alias_code = Column(Text, nullable=False, unique=True)
    device_group_id = Column(
        BigInteger,
        ForeignKey("device_groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_active = Column(Boolean, nullable=False, server_default="true")

    device_group = relationship("DeviceGroup", back_populates="aliases")