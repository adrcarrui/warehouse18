from sqlalchemy import Column, BigInteger, Text, Boolean, SmallInteger
from .base import Base

class MovementType(Base):
    __tablename__ = "movement_types"

    id = Column(BigInteger, primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)

    affects_stock = Column(Boolean, nullable=False)
    affects_location = Column(Boolean, nullable=False)
    stock_sign = Column(SmallInteger, nullable=False)  # -1, 0, 1
