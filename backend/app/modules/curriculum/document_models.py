"""Curricular evidence files, scoped to a school, year, level, grade and subject.

A document attachment is NOT a structured/official curriculum framework: it needs
human review and cannot silently alter classroom planning or student exercises.
"""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.types import UTCDateTime


class CurriculumDocument(Base):
    __tablename__ = "curriculum_documents"
    __table_args__ = (
        CheckConstraint("education_level IN ('PRIMARIA','SECUNDARIA')", name="ck_currdoc_level"),
        CheckConstraint("grade_number BETWEEN 1 AND 6", name="ck_currdoc_grade"),
        CheckConstraint("academic_year BETWEEN 2020 AND 2100", name="ck_currdoc_year"),
        CheckConstraint("file_size > 0 AND file_size <= 4194304", name="ck_currdoc_size"),
        Index("ix_currdoc_scope", "school_id", "academic_year", "education_level", "grade_number", "area"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="RESTRICT"))
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    education_level: Mapped[str] = mapped_column(String(16))
    grade_number: Mapped[int] = mapped_column(Integer)
    academic_year: Mapped[int] = mapped_column(Integer)
    area: Mapped[str] = mapped_column(String(80))
    filename: Mapped[str] = mapped_column(String(180))
    media_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    file_data: Mapped[bytes] = mapped_column(LargeBinary)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", server_default="PENDING")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
