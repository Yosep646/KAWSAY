import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class SupportFlag(Base):
    __tablename__ = "support_flags"
    __table_args__ = (
        CheckConstraint("status IN ('OPEN','ACKNOWLEDGED','RESOLVED','DISMISSED')", name="ck_flag_status"),
        # un solo flag activo por (estudiante, competencia, regla): la evidencia se actualiza, no se duplica
        Index("uq_active_flag", "student_user_id", "competency_id", "rule_id", unique=True,
              sqlite_where=text("status IN ('OPEN','ACKNOWLEDGED')")),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("competencies.id", ondelete="RESTRICT"))
    rule_id: Mapped[str] = mapped_column(String(32))
    rule_version: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="OPEN", server_default="OPEN")
    evidence: Mapped[Any] = mapped_column(JSON)
    recommendation_code: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
