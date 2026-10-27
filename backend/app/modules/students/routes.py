import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.modules.audit.service import log_access
from app.modules.students import service
from app.modules.students.email_models import StudentEmailLogin
from app.modules.users.models import Role, User

router = APIRouter(prefix="/students", tags=["students"])
DB = Annotated[Session, Depends(get_db)]
Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]


class StudentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=120)
    grade_id: int = Field(ge=1)
    classroom_id: uuid.UUID
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=12, max_length=128)

    @model_validator(mode="after")
    def require_both(self):
        if (self.email is None) != (self.password is None):
            raise ValueError("Ingresa el correo y la contraseña juntos")
        return self


class StudentCredentials(BaseModel):
    id: uuid.UUID
    display_name: str
    grade_id: int
    login_code: str | None = None
    pin: str | None = None  # el PIN solo se emite una vez en modo tradicional
    email: EmailStr | None = None


class StudentOut(BaseModel):
    id: uuid.UUID
    display_name: str
    grade_id: int
    login_code: str | None
    email: EmailStr | None = None


class PasswordResetIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=12, max_length=128)


class PinOut(BaseModel):
    pin: str


@router.post("", response_model=StudentCredentials, status_code=201)
def create(body: StudentCreate, db: DB, teacher: Teacher) -> dict:
    user, pin = service.create_student(db, teacher, body.display_name, body.grade_id, body.classroom_id,
                                       str(body.email) if body.email else None, body.password)
    return {"id": user.id, "display_name": user.display_name, "grade_id": body.grade_id,
            "login_code": user.login_code if pin else None, "pin": pin,
            "email": str(body.email).lower() if body.email else None}


@router.get("/{student_id}", response_model=StudentOut)
def get_one(student_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    user, profile = service.get_accessible_student(db, teacher, student_id)
    log_access(db, teacher, "students.read", "student", student_id)
    entry = db.get(StudentEmailLogin, user.id)
    return {"id": user.id, "display_name": user.display_name, "grade_id": profile.grade_id,
            "login_code": user.login_code if entry is None else None,
            "email": entry.email if entry else None}


@router.post("/{student_id}/reset-pin", response_model=PinOut)
def reset_pin(student_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    return {"pin": service.reset_pin(db, teacher, student_id)}


@router.post("/{student_id}/reset-password", status_code=204)
def reset_password(student_id: uuid.UUID, body: PasswordResetIn, db: DB, teacher: Teacher):
    service.reset_student_password(db, teacher, student_id, body.password)
