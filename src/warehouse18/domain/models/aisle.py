from sqlalchemy import Column, BigInteger, Text, Boolean, Integer

from .base import Base


class Aisle(Base):
    __tablename__ = "aisles"

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")