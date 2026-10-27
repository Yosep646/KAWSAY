import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class Language(Base):
    __tablename__ = "languages"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)
    name: Mapped[str] = mapped_column(String(80))


class LanguageVariant(Base):
    """Variante dialectal (p. ej. de quechua). Se registra por especialistas; no se asume que sean idénticas."""

    __tablename__ = "language_variants"
    __table_args__ = (UniqueConstraint("language_id", "code", name="uq_language_variant"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id", ondelete="RESTRICT"))
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(Text)


class StudentLanguage(Base):
    """Declaradas explícitamente (nunca inferidas por ubicación)."""

    __tablename__ = "student_languages"
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True)
    mother_language_id: Mapped[int | None] = mapped_column(ForeignKey("languages.id", ondelete="RESTRICT"))
    mother_variant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("language_variants.id", ondelete="RESTRICT"))
    preferred_language_id: Mapped[int | None] = mapped_column(ForeignKey("languages.id", ondelete="RESTRICT"))
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(), onupdate=func.now())


class VariantTranslation(Base):
    """Traducción escrita por una persona y verificada por un revisor. No se genera ni se inventa automáticamente."""

    __tablename__ = "variant_translations"
    __table_args__ = (
        UniqueConstraint("variant_id", "language_id", name="uq_translation_variant_language"),
        CheckConstraint("status IN ('DRAFT','IN_REVIEW','VERIFIED','REJECTED')", name="ck_translation_status"),
        CheckConstraint("status <> 'VERIFIED' OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
                        name="ck_translation_verified_by"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignment_variants.id", ondelete="RESTRICT"))
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id", ondelete="RESTRICT"))
    language_variant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("language_variants.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(300))
    instructions: Mapped[str] = mapped_column(Text)
    question_prompts: Mapped[Any] = mapped_column(JSON, default=dict, server_default="{}")  # {question_id: texto}
    status: Mapped[str] = mapped_column(String(12), default="DRAFT", server_default="DRAFT")
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
