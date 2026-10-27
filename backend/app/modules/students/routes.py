import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.modules.audit.service import log_access
from app.modules.students import service
from app.modules.users.models import Role, User

router = APIRouter(prefix="/students", tags=["students"])
DB = Annotated[Session, Depends(get_db)]
Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]


class StudentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=120)
    grade_id: int = Field(ge=1)
    classroom_id: uuid.UUID


class StudentCredentials(BaseModel):
    id: uuid.UUID
    display_name: str
    grade_id: int
    login_code: str
    pin: str  # se muestra UNA sola vez; en BD solo queda el hash


class StudentOut(BaseModel):
    id: uuid.UUID
    display_name: str
    grade_id: int
    login_code: str | None


class PinOut(BaseModel):
    pin: str


@router.post("", response_model=StudentCredentials, status_code=201)
def create(body: StudentCreate, db: DB, teacher: Teacher) -> dict:
    user, pin = service.create_student(db, teacher, body.display_name, body.grade_id, body.classroom_id)
    return {"id": user.id, "display_name": user.display_name, "grade_id": body.grade_id,
            "login_code": user.login_code, "pin": pin}


@router.get("/{student_id}", response_model=StudentOut)
def get_one(student_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    user, profile = service.get_accessible_student(db, teacher, student_id)
    log_access(db, teacher, "students.read", "student", student_id)
    return {"id": user.id, "display_name": user.display_name, "grade_id": profile.grade_id,
            "login_code": user.login_code}


@router.post("/{student_id}/reset-pin", response_model=PinOut)
def reset_pin(student_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    return {"pin": service.reset_pin(db, teacher, student_id)}
