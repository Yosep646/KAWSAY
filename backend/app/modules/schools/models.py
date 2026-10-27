import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import UTCDateTime


class UgelUnit(Base):
    __tablename__ = "ugel_units"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    region: Mapped[str] = mapped_column(String(120))
    code: Mapped[str | None] = mapped_column(String(32), unique=True)


class School(Base):
    __tablename__ = "schools"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str | None] = mapped_column(String(32), unique=True)
    ugel_unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ugel_units.id", ondelete="RESTRICT", name="fk_schools_ugel_unit"))
    region: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.now(),
                                                 onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
