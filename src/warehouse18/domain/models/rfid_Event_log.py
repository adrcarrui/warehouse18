from sqlalchemy import Column, BigInteger, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class RfidEventLog(Base):
    __tablename__ = "rfid_event_log"

    id = Column(BigInteger, primary_key=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    epc = Column(Text, nullable=True, index=True)
    reader_id = Column(Text, nullable=True, index=True)
    antenna = Column(BigInteger, nullable=True, index=True)

    door_id = Column(Text, nullable=True, index=True)
    zone_id = Column(Text, nullable=True, index=True)
    zone_role = Column(Text, nullable=True, index=True)

    event_type = Column(Text, nullable=False, index=True)
    reason = Column(Text, nullable=True, index=True)

    movement_code = Column(Text, nullable=True, index=True)
    movement_id = Column(BigInteger, nullable=True, index=True)

    user_id = Column(BigInteger, nullable=True, index=True)
    mysim_user_id = Column(BigInteger, nullable=True, index=True)

    payload_json = Column(JSONB, nullable=True)

    seen_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now(), index=True)