import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_roles
from app.modules.classrooms.service import get_teacher_classroom
from app.modules.planning import service
from app.modules.users.models import Role, User

router = APIRouter(prefix="/planning", tags=["planning"])
DB = Annotated[Session, Depends(get_db)]
Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]
Staff = Annotated[User, Depends(require_roles(Role.TEACHER, Role.ADMIN))]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlanIn(_In):
    academic_year: int = Field(ge=2020, le=2100)
    framework_id: uuid.UUID
    name: str = Field(min_length=2, max_length=200)


class PeriodIn(_In):
    name: str = Field(min_length=1, max_length=100)
    sequence: int = Field(ge=1, le=12)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def _dates(self) -> "PeriodIn":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date no puede ser anterior a start_date")
        return self


class UnitIn(_In):
    period_id: uuid.UUID
    grade_id: int = Field(ge=1)
    subject_id: uuid.UUID
    title: str = Field(min_length=2, max_length=300)
    sequence: int = Field(default=1, ge=1)


class TopicIn(_In):
    unit_id: uuid.UUID
    competency_id: uuid.UUID
    capacity_id: uuid.UUID | None = None
    title: str = Field(min_length=2, max_length=300)
    learning_objective: str = Field(min_length=5, max_length=2000)
    sequence: int = Field(default=1, ge=1)


def _ver(v) -> dict:
    return {"id": v.id, "plan_id": v.plan_id, "label": v.label, "status": v.status}


@router.post("/plans", status_code=201)
def create_plan(body: PlanIn, db: DB, teacher: Teacher) -> dict:
    plan, ver = service.create_plan(db, teacher, body.academic_year, body.framework_id, body.name)
    return {"id": plan.id, "version": _ver(ver)}


@router.get("/plans")
def list_plans(db: DB, user: Staff) -> list[dict]:
    return service.list_plans(db, user)


@router.post("/plans/{plan_id}/versions", status_code=201)
def new_version(plan_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    return _ver(service.new_version(db, teacher, plan_id))


@router.get("/versions/{version_id}")
def get_version(version_id: uuid.UUID, db: DB, user: Staff) -> dict:
    ver, _ = service.get_version(db, user, version_id)
    return service.version_tree(db, ver)


@router.post("/versions/{version_id}/periods", status_code=201)
def add_period(version_id: uuid.UUID, body: PeriodIn, db: DB, teacher: Teacher) -> dict:
    p = service.add_period(db, teacher, version_id, body.name, body.sequence, body.start_date, body.end_date)
    return {"id": p.id}


@router.post("/versions/{version_id}/units", status_code=201)
def add_unit(version_id: uuid.UUID, body: UnitIn, db: DB, teacher: Teacher) -> dict:
    u = service.add_unit(db, teacher, version_id, body.period_id, body.grade_id, body.subject_id, body.title,
                         body.sequence)
    return {"id": u.id}


@router.post("/versions/{version_id}/topics", status_code=201)
def add_topic(version_id: uuid.UUID, body: TopicIn, db: DB, teacher: Teacher) -> dict:
    t = service.add_topic(db, teacher, version_id, body.unit_id, body.competency_id, body.capacity_id, body.title,
                          body.learning_objective, body.sequence)
    return {"id": t.id}


@router.post("/versions/{version_id}/submit")
def submit(version_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    return _ver(service.submit(db, teacher, version_id))


@router.post("/versions/{version_id}/reject")
def reject(version_id: uuid.UUID, db: DB, admin: Admin) -> dict:
    return _ver(service.reject(db, admin, version_id))


@router.post("/versions/{version_id}/approve")
def approve(version_id: uuid.UUID, db: DB, admin: Admin) -> dict:
    return _ver(service.approve(db, admin, version_id))


@router.post("/versions/{version_id}/activate")
def activate(version_id: uuid.UUID, db: DB, admin: Admin) -> dict:
    return _ver(service.activate(db, admin, version_id))


@router.get("/active")
def active_for_classroom(classroom_id: Annotated[uuid.UUID, Query()], db: DB, teacher: Teacher) -> list[dict]:
    """Planificación vigente (versión ACTIVE) de la institución para el año del aula."""
    room = get_teacher_classroom(db, teacher.id, classroom_id)
    return [service.version_tree(db, v)
            for v in service.active_versions_for_school_year(db, room.school_id, room.academic_year)]


_ = get_current_user
