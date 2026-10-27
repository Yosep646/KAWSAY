import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import require_roles
from app.modules.schools.models import School, UgelUnit
from app.modules.users.models import Role, User

router = APIRouter(prefix="/schools", tags=["schools"])
DB = Annotated[Session, Depends(get_db)]
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]


class SchoolIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=200)
    code: str | None = Field(default=None, max_length=32)
    ugel_unit_id: uuid.UUID | None = None
    region: str | None = Field(default=None, max_length=120)


class SchoolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    code: str | None
    ugel_unit_id: uuid.UUID | None
    region: str | None
    created_at: datetime


class UgelIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=200)
    region: str = Field(min_length=2, max_length=120)
    code: str | None = Field(default=None, max_length=32)


class UgelOut(UgelIn):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: uuid.UUID


@router.post("/ugel-units", response_model=UgelOut, status_code=201)
def create_ugel(body: UgelIn, db: DB, _: Admin) -> UgelUnit:
    unit = UgelUnit(**body.model_dump())
    db.add(unit)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("El código de UGEL ya existe") from exc
    return unit


@router.post("", response_model=SchoolOut, status_code=201)
def create_school(body: SchoolIn, db: DB, _: Admin) -> School:
    if body.ugel_unit_id is not None and db.get(UgelUnit, body.ugel_unit_id) is None:
        raise NotFoundError("UGEL no encontrada")
    school = School(**body.model_dump())
    db.add(school)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("El código de escuela ya existe") from exc
    return school


@router.get("", response_model=list[SchoolOut])
def list_schools(db: DB, _: Admin, limit: Annotated[int, Query(ge=1, le=100)] = 50,
                 offset: Annotated[int, Query(ge=0)] = 0) -> list[School]:
    return list(db.scalars(select(School).where(School.deleted_at.is_(None))
                           .order_by(School.name, School.id).limit(limit).offset(offset)))
