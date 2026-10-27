import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime

VARIANT_STATUSES = ("DRAFT", "AI_GENERATED", "TEACHER_REVIEW", "APPROVED", "PUBLISHED")


class Assignment(Base):
    """Tarea del docente. Conserva la trazabilidad curricular: escuela, aula, versión de planificación,
    área, docente, modo y estado. Año/periodo/grado/competencia/tema/objetivo viven en cada variante."""

    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint("mode IN ('MANUAL','AI_ASSISTED','ADAPTIVE_POOL')", name="ck_assignment_mode"),
        CheckConstraint("status IN ('DRAFT','PUBLISHED','ARCHIVED')", name="ck_assignment_status"),
        Index("ix_assignment_classroom_status", "classroom_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="RESTRICT"))
    classroom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classrooms.id", ondelete="RESTRICT"))
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    plan_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_plan_versions.id", ondelete="RESTRICT"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    mode: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(300))
    base_instructions: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", server_default="DRAFT")
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())


class AssignmentVariant(Base):
    """Una variante por grado. El contenido generado por IA entra como AI_GENERATED y NO puede
    aprobarse ni publicarse sin pasar por TEACHER_REVIEW + aprobación de un docente (approved_by)."""

    __tablename__ = "assignment_variants"
    __table_args__ = (
        UniqueConstraint("assignment_id", "grade_id", "version", name="uq_variant_assignment_grade_version"),
        CheckConstraint("status IN ('DRAFT','AI_GENERATED','TEACHER_REVIEW','APPROVED','PUBLISHED')", name="ck_variant_status"),
        CheckConstraint("source IN ('TEACHER','AI','AI_EDITED')", name="ck_variant_source"),
        CheckConstraint("status NOT IN ('APPROVED','PUBLISHED') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)",
                        name="ck_variant_human_approval"),
        CheckConstraint("source <> 'AI' OR generated_by IS NOT NULL", name="ck_variant_ai_provenance"),
        CheckConstraint("validation_status IN ('NOT_CHECKED','OK','NEEDS_REVIEW')", name="ck_variant_validation"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignments.id", ondelete="RESTRICT"), index=True)
    grade_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("grades.id", ondelete="RESTRICT"))
    version: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_topics.id", ondelete="RESTRICT"))
    competency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("competencies.id", ondelete="RESTRICT"))
    period_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_periods.id", ondelete="RESTRICT"))
    learning_objective: Mapped[str] = mapped_column(Text)  # instantánea: no cambia si cambia la planificación
    title: Mapped[str] = mapped_column(String(300))
    instructions: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", server_default="DRAFT")
    source: Mapped[str] = mapped_column(String(12), default="TEACHER", server_default="TEACHER")
    generated_by: Mapped[str | None] = mapped_column(String(120))  # proveedor/modelo/versión de prompt
    validation_status: Mapped[str] = mapped_column(String(14), default="NOT_CHECKED", server_default="NOT_CHECKED")
    validation_notes: Mapped[Any | None] = mapped_column(JSON)    # motivos de NEEDS_REVIEW (CurriculumValidator)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    approved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("variant_id", "position", name="uq_question_position"),
        CheckConstraint("type IN ('MULTIPLE_CHOICE','NUMERIC','SHORT_TEXT')", name="ck_question_type"),
        CheckConstraint("difficulty BETWEEN 1 AND 3", name="ck_question_difficulty"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignment_variants.id", ondelete="RESTRICT"), index=True)
    position: Mapped[int] = mapped_column(SmallInteger)
    type: Mapped[str] = mapped_column(String(16))
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[Any | None] = mapped_column(JSON)
    correct_answer: Mapped[Any] = mapped_column(JSON)
    hints: Mapped[Any] = mapped_column(JSON, default=list, server_default="[]")  # pistas docentes, usables offline
    explanation: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(SmallInteger, default=2, server_default="2")


class StudentAssignment(Base):
    __tablename__ = "student_assignments"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_user_id", name="uq_student_assignment"),
        CheckConstraint("status IN ('ASSIGNED','IN_PROGRESS','COMPLETED')", name="ck_student_assignment_status"),
        CheckConstraint("origin IN ('TEACHER','SELF')", name="ck_student_assignment_origin"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignments.id", ondelete="RESTRICT"))
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignment_variants.id", ondelete="RESTRICT"))
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    seq: Mapped[int] = mapped_column(BigInteger, index=True)  # cursor monótono para sync pull (ver next_seq)
    status: Mapped[str] = mapped_column(String(16), default="ASSIGNED", server_default="ASSIGNED")
    origin: Mapped[str] = mapped_column(String(8), default="TEACHER", server_default="TEACHER")  # TEACHER=asignada, SELF="Quiero aprender"
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())


class Counter(Base):
    """Contadores monótonos (SQLite no tiene secuencias). Se incrementan dentro de la transacción de escritura."""

    __tablename__ = "counters"
    name: Mapped[str] = mapped_column(String(40), primary_key=True)
    value: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
