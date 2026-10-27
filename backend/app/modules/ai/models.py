import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class AIGenerationRequest(Base):
    """Trazabilidad de uso de IA. NO guarda el contenido ni datos personales: solo metadatos."""

    __tablename__ = "ai_generation_requests"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignments.id", ondelete="RESTRICT"))
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignment_variants.id", ondelete="RESTRICT"))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str | None] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))  # GENERATED / NEEDS_REVIEW / INVALID_OUTPUT / UNAVAILABLE / TIMEOUT
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
