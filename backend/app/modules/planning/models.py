import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime

VERSION_STATUSES = ("DRAFT", "UNDER_REVIEW", "APPROVED", "ACTIVE", "ARCHIVED")


class AcademicYear(Base):
    __tablename__ = "academic_years"
    __table_args__ = (UniqueConstraint("school_id", "year", name="uq_academic_year_school"),
                      CheckConstraint("year BETWEEN 2020 AND 2100", name="ck_academic_year"))
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="RESTRICT"))
    year: Mapped[int] = mapped_column(SmallInteger)


class SchoolCurriculumPlan(Base):
    __tablename__ = "school_curriculum_plans"
    __table_args__ = (UniqueConstraint("school_id", "academic_year_id", "name", name="uq_plan_school_year_name"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="RESTRICT"), index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_years.id", ondelete="RESTRICT"))
    framework_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_frameworks.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())


class CurriculumPlanVersion(Base):
    __tablename__ = "curriculum_plan_versions"
    __table_args__ = (
        UniqueConstraint("plan_id", "label", name="uq_plan_version_label"),
        CheckConstraint("status IN ('DRAFT','UNDER_REVIEW','APPROVED','ACTIVE','ARCHIVED')", name="ck_plan_version_status"),
        CheckConstraint("status NOT IN ('APPROVED','ACTIVE') OR approved_by IS NOT NULL",
                        name="ck_plan_version_approver"),
        # a lo sumo UNA versión ACTIVE por plan, garantizado por la BD
        Index("uq_one_active_version_per_plan", "plan_id", unique=True, sqlite_where=text("status = 'ACTIVE'")),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("school_curriculum_plans.id", ondelete="RESTRICT"))
    label: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", server_default="DRAFT")
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    approved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    activated_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())


class AcademicPeriod(Base):
    __tablename__ = "academic_periods"
    __table_args__ = (UniqueConstraint("version_id", "sequence", name="uq_period_sequence"),
                      CheckConstraint("end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
                                      name="ck_period_dates"))
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_plan_versions.id", ondelete="RESTRICT"),
                                                  index=True)
    name: Mapped[str] = mapped_column(String(100))
    sequence: Mapped[int] = mapped_column(SmallInteger)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)


class CurriculumUnit(Base):
    __tablename__ = "curriculum_units"
    __table_args__ = (Index("ix_unit_version_grade_subject", "version_id", "grade_id", "subject_id"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_plan_versions.id", ondelete="RESTRICT"))
    period_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_periods.id", ondelete="RESTRICT"))
    grade_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("grades.id", ondelete="RESTRICT"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(300))
    sequence: Mapped[int] = mapped_column(SmallInteger, default=1)


class CurriculumTopic(Base):
    __tablename__ = "curriculum_topics"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_units.id", ondelete="RESTRICT"), index=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("competencies.id", ondelete="RESTRICT"))
    capacity_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("capacities.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(300))
    learning_objective: Mapped[str] = mapped_column(Text)
    sequence: Mapped[int] = mapped_column(SmallInteger, default=1)
