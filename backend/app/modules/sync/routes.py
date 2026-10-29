import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.permissions import require_roles
from app.domain import adaptive
from app.modules.assignments.models import StudentAssignment
from app.modules.learning.models import LearningAttempt
from app.modules.sync import service
from app.modules.users.models import Role, User

router = APIRouter(prefix="/sync", tags=["sync"])
Student = Annotated[User, Depends(require_roles(Role.STUDENT))]
DB = Annotated[Session, Depends(get_db)]


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(max_length=64)
    type: str = Field(max_length=40)
    payload: dict[str, Any] = Field(default_factory=dict)


class PushIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_id: uuid.UUID
    events: list[EventIn] = Field(min_length=1, max_length=service.MAX_BATCH)


@router.post("/push")
def push(body: PushIn, db: DB, student: Student) -> dict:
    """Idempotente: el mismo event_id enviado N veces produce 1 solo registro (resto = DUPLICATE)."""
    results = service.push(db, student, body.device_id, [e.model_dump() for e in body.events])
    return {"results": results}


@router.get("/pull")
def pull(db: DB, student: Student, cursor: Annotated[int, Query(ge=0)] = 0,
         limit: Annotated[int, Query(ge=1, le=50)] = 20) -> dict:
    return service.pull(db, student, cursor, limit)


@router.get("/courses")
def my_courses(db: DB, student: Student) -> list[dict]:
    """Áreas activas del grado y aula del alumno; accesibles antes de publicar tareas."""
    from app.modules.sync.courses import student_courses
    return student_courses(db, student.id)


@router.get("/tasks/{student_assignment_id}/attempts")
def task_attempts(student_assignment_id: uuid.UUID, device_id: uuid.UUID, db: DB, student: Student) -> dict:
    """Estado propio para reanudar una actividad en línea, sin devolver respuestas."""
    task = db.get(StudentAssignment, student_assignment_id)
    if task is None or task.student_user_id != student.id:
        raise NotFoundError("Actividad no encontrada")
    rows = list(db.scalars(select(LearningAttempt).where(
        LearningAttempt.student_assignment_id == task.id, LearningAttempt.student_user_id == student.id)))
    facts = [adaptive.AttemptFact(str(a.id), str(a.question_id), a.attempt_number, a.is_correct,
                                  a.hints_used, a.effective_at) for a in rows]
    results = adaptive.question_results(facts)
    return {"questions": [{"question_id": r.question_id, "closed": r.closed,
                           "device_attempt_number": max((a.attempt_number for a in rows
                                                         if str(a.question_id) == r.question_id and a.device_id == device_id),
                                                        default=0)} for r in results]}
