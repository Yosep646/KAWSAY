import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class Grade(Base):
    """Estructura de grados (dato estructural, NO currículo). Primaria 1-6, Secundaria 1-5."""

    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("level", "number", name="uq_grades_level_number"),
        CheckConstraint("level IN ('PRIMARIA','SECUNDARIA')", name="ck_grades_level"),
        CheckConstraint("number BETWEEN 1 AND 6", name="ck_grades_number"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # INTEGER: alias de rowid en SQLite
    level: Mapped[str] = mapped_column(String(16))
    number: Mapped[int] = mapped_column(SmallInteger)


class CurriculumFramework(Base):
    """Referencia curricular (p. ej. CNEB). `is_demo` es obligatorio: los datos de muestra
    nunca se presentan como currículo oficial."""

    __tablename__ = "curriculum_frameworks"
    __table_args__ = (UniqueConstraint("country_code", "name", "version_label", name="uq_framework"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    country_code: Mapped[str] = mapped_column(String(2))
    name: Mapped[str] = mapped_column(String(200))
    version_label: Mapped[str] = mapped_column(String(50))
    is_demo: Mapped[bool] = mapped_column(Boolean)
    source_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("framework_id", "name", name="uq_subject_framework_name"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    framework_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_frameworks.id", ondelete="RESTRICT"),
                                                    index=True)
    name: Mapped[str] = mapped_column(String(200))


class Competency(Base):
    __tablename__ = "competencies"
    __table_args__ = (UniqueConstraint("subject_id", "name", name="uq_competency_subject_name"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"), index=True)
    code: Mapped[str | None] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(300))


class Capacity(Base):
    __tablename__ = "capacities"
    __table_args__ = (UniqueConstraint("competency_id", "name", name="uq_capacity_competency_name"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    competency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("competencies.id", ondelete="RESTRICT"),
                                                     index=True)
    name: Mapped[str] = mapped_column(String(300))
