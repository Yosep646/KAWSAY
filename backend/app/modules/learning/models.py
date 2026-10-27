import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class LearningAttempt(Base):
    """Append-only (trigger en BD). `id` = event_id generado en el cliente => clave de idempotencia."""

    __tablename__ = "learning_attempts"
    __table_args__ = (
        CheckConstraint("attempt_number >= 1", name="ck_attempt_number"),
        CheckConstraint("hints_used >= 0", name="ck_attempt_hints"),
        CheckConstraint("response_time_ms >= 0", name="ck_attempt_time"),
        UniqueConstraint("student_assignment_id", "question_id", "attempt_number", "device_id", name="uq_attempt_slot"),
        Index("ix_attempt_student_comp_time", "student_user_id", "competency_id", "effective_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    student_assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_assignments.id", ondelete="RESTRICT"))
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="RESTRICT"))
    competency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("competencies.id", ondelete="RESTRICT"))
    device_id: Mapped[uuid.UUID] = mapped_column()
    attempt_number: Mapped[int] = mapped_column(SmallInteger)
    answer: Mapped[Any] = mapped_column(JSON)
    is_correct: Mapped[bool] = mapped_column(Boolean)                 # calculado por el SERVIDOR
    client_is_correct: Mapped[bool | None] = mapped_column(Boolean)   # lo que afirmó el cliente (auditoría)
    hints_used: Mapped[int] = mapped_column(SmallInteger)
    response_time_ms: Mapped[int] = mapped_column(Integer)
    client_created_at: Mapped[datetime] = mapped_column(UTCDateTime())
    effective_at: Mapped[datetime] = mapped_column(UTCDateTime())  # min(reloj cliente, recepción)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())


class StudentCompetencyProgress(Base):
    __tablename__ = "student_competency_progress"
    __table_args__ = (UniqueConstraint("student_user_id", "competency_id", name="uq_progress_student_competency"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    competency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("competencies.id", ondelete="RESTRICT"))
    score: Mapped[float | None] = mapped_column(Numeric(5, 4, asdecimal=False))   # NULL = sin evidencia suficiente
    evidence_count: Mapped[int] = mapped_column(Integer)
    state: Mapped[str | None] = mapped_column(String(12))          # REFUERZO/ESPERADO/DESAFIO (interno)
    method_version: Mapped[str] = mapped_column(String(32))
    computed_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
