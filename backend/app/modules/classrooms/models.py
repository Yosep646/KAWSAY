import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class Classroom(Base):
    __tablename__ = "classrooms"
    __table_args__ = (
        UniqueConstraint("school_id", "academic_year", "name", name="uq_classroom_school_year_name"),
        CheckConstraint("academic_year BETWEEN 2020 AND 2100", name="ck_classroom_year"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    academic_year: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class ClassroomTeacher(Base):
    __tablename__ = "classroom_teachers"
    classroom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classrooms.id", ondelete="RESTRICT"),
                                                    primary_key=True)
    teacher_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"),
                                                       primary_key=True, index=True)


class ClassroomStudent(Base):
    __tablename__ = "classroom_students"
    classroom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classrooms.id", ondelete="RESTRICT"),
                                                    primary_key=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"),
                                                       primary_key=True, index=True)
    joined_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    left_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
