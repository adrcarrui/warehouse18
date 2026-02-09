from sqlalchemy import Column, BigInteger, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False)
    parent_id = Column(BigInteger, ForeignKey("locations.id"), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")

    parent = relationship(
        "Location",
        remote_side=[id],
        backref="children",
    )
