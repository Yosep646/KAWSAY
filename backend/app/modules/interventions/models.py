import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class TeacherIntervention(Base):
    __tablename__ = "teacher_interventions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("competencies.id", ondelete="RESTRICT"))
    support_flag_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("support_flags.id", ondelete="RESTRICT"))
    strategy: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(Text)
    score_at_creation: Mapped[float | None] = mapped_column(Numeric(5, 4, asdecimal=False))  # para mostrar evolución observada
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
