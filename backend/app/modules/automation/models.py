import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class DomainEvent(Base):
    """Outbox transaccional: el evento se guarda en la MISMA transacción que el cambio de dominio.
    Si n8n cae, los eventos esperan; el núcleo no se ve afectado."""

    __tablename__ = "domain_events"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','DELIVERED','FAILED')", name="ck_event_status"),
        Index("ix_event_pending", "status", "next_attempt_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(60))
    payload: Mapped[Any] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(10), default="PENDING", server_default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    next_attempt_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
