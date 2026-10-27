import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.modules.audit.service import log_access
from app.modules.classrooms import service
from app.modules.classrooms.models import Classroom
from app.modules.users.models import Role, User

router = APIRouter(prefix="/classrooms", tags=["classrooms"])
DB = Annotated[Session, Depends(get_db)]
Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]


class ClassroomIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    academic_year: int = Field(ge=2020, le=2100)


class ClassroomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    academic_year: int
    created_at: datetime


class StudentBrief(BaseModel):
    id: uuid.UUID
    display_name: str
    grade_id: int
    grade_level: str
    grade_number: int


class ClassroomDetail(ClassroomOut):
    students: list[StudentBrief]
    grades_present: list[str]


@router.post("", response_model=ClassroomOut, status_code=201)
def create(body: ClassroomIn, db: DB, teacher: Teacher) -> Classroom:
    return service.create_classroom(db, teacher, body.name, body.academic_year)


@router.get("", response_model=list[ClassroomOut])
def list_mine(db: DB, teacher: Teacher) -> list[Classroom]:
    return service.list_teacher_classrooms(db, teacher.id)


@router.get("/{classroom_id}", response_model=ClassroomDetail)
def detail(classroom_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    room = service.get_teacher_classroom(db, teacher.id, classroom_id)
    log_access(db, teacher, "classrooms.read", "classroom", room.id)
    students = service.classroom_students(db, room.id)
    grades = sorted({f"{s['grade_number']}.º {s['grade_level']}" for s in students})
    return {**ClassroomOut.model_validate(room).model_dump(), "students": students, "grades_present": grades}
