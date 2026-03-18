from sqlalchemy import Column, BigInteger, Text, DateTime, Numeric, ForeignKey, String, func
from .base import Base

class Movement(Base):
    __tablename__ = "movements"

    id = Column(BigInteger, primary_key=True)

    movement_type_id = Column(BigInteger, ForeignKey("movement_types.id", ondelete="RESTRICT"), nullable=False)

    item_id = Column(BigInteger, ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Numeric(18, 6), nullable=True)

    from_location_id = Column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    to_location_id = Column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)

    reference_type = Column(Text, nullable=True)  # asset/container
    reference_id = Column(BigInteger, nullable=True)

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notes = Column(Text, nullable=True)

    item_key = Column(Text, nullable=True)  # denormalized for easier querying
    mysim_user_id = Column(BigInteger, nullable=True, index=True)  # denormalized for easier querying

    review_status = Column(String(20), nullable=False, default="pending")
    review_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id = Column(BigInteger, nullable=True)

    mysim_sync_status = Column(String(20), nullable=False, default="not_sent")
    mysim_synced_at = Column(DateTime(timezone=True), nullable=True)
    mysim_sync_error = Column(Text, nullable=True)