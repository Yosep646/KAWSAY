import uuid

from sqlalchemy import ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StudentProfile(Base):
    """El grado es del ESTUDIANTE (no del aula): permite aulas multigrado."""

    __tablename__ = "student_profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="RESTRICT"), index=True)
    grade_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("grades.id", ondelete="RESTRICT"),
                                          index=True)
