"""Acceso opcional por correo para estudiantes sin alterar el modelo código/PIN legacy."""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class StudentEmailLogin(Base):
    __tablename__ = "student_email_logins"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True
    )
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), nullable=False
    )
