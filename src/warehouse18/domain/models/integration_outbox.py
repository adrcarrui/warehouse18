from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from warehouse18.infrastructure.db import Base


class IntegrationOutbox(Base):
    __tablename__ = "integration_outbox"

    __table_args__ = (
        CheckConstraint(
            "direction = ANY (ARRAY['outbound'::text, 'inbound'::text])",
            name="outbox_direction_ck",
        ),
        CheckConstraint(
            "retries >= 0",
            name="outbox_retries_ck",
        ),
        CheckConstraint(
            "status = ANY (ARRAY['pending'::text, 'processing'::text, 'sent'::text, 'error'::text])",
            name="outbox_status_ck",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    direction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'outbound'"),
    )

    target_system: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'external_api'"),
    )

    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)

    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'pending'"),
    )

    retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        default=lambda: datetime.now(timezone.utc),
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )