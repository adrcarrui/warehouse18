from sqlalchemy import BigInteger, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RfidEventLog(Base):
    __tablename__ = "rfid_event_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    seen_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        index=True,
    )

    epc: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    reader_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    antenna: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    door_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    zone_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    zone_role: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    event_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    movement_code: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    movement_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    mysim_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    review_status: Mapped[str] = mapped_column(Text, nullable=False, server_default="confirmed", index=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)