from sqlalchemy import Column, BigInteger, Text, Boolean, Integer
from sqlalchemy.orm import relationship


from .base import Base


class Aisle(Base):
    __tablename__ = "aisles"

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")

    locations = relationship("Location", back_populates="aisle")

    allowed_device_groups = relationship(
        "AisleDeviceGroup",
        back_populates="aisle",
        cascade="all, delete-orphan",
    )