import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class SyncEvent(Base):
    """Registro de eventos recibidos: UNIQUE(event_id) => idempotencia, también para rechazos."""

    __tablename__ = "sync_events"
    __table_args__ = (CheckConstraint("status IN ('ACKED','REJECTED')", name="ck_sync_event_status"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(unique=True)
    device_id: Mapped[uuid.UUID] = mapped_column()
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(10))
    reason: Mapped[str | None] = mapped_column(String(80))
    received_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
