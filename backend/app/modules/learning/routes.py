"""QUIERO APRENDER: el estudiante elige qué practicar DENTRO del contenido disponible:
solo variantes PUBLICADAS por docentes de su escuela, de SU grado, alineadas a la planificación. Nada se inventa."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.permissions import require_roles
from app.modules.assignments.models import Assignment, AssignmentVariant, Question, StudentAssignment
from app.modules.assignments.service import next_seq
from app.modules.curriculum.models import Competency, Subject
from app.modules.learning.models import StudentCompetencyProgress
from app.modules.planning.models import CurriculumTopic
from app.modules.students.models import StudentProfile
from app.modules.sync.service import preferred_language, task_payload
from app.modules.users.models import Role, User

router = APIRouter(prefix="/learning", tags=["learning"])
Student = Annotated[User, Depends(require_roles(Role.STUDENT))]
DB = Annotated[Session, Depends(get_db)]


class StartIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    variant_id: uuid.UUID


def _available(db: Session, student: User) -> Select[AssignmentVariant, Assignment]:
    prof = db.scalar(select(StudentProfile).where(StudentProfile.user_id == student.id))
    if prof is None:
        raise NotFoundError("Perfil de estudiante no encontrado")
    return (select(AssignmentVariant, Assignment).join(Assignment, Assignment.id == AssignmentVariant.assignment_id)
            .where(AssignmentVariant.status == "PUBLISHED", AssignmentVariant.grade_id == prof.grade_id,
                   Assignment.school_id == prof.school_id))


@router.get("/subjects")
def subjects(db: DB, student: Student) -> list[dict]:
    base = _available(db, student).subquery()
    q = (select(Subject.id, Subject.name, func.count(base.c.id)).join(base, base.c.subject_id == Subject.id)
         .group_by(Subject.id, Subject.name).order_by(Subject.name))
    return [{"id": i, "name": n, "activities": c} for i, n, c in db.execute(q)]


@router.get("/topics")
def topics(subject_id: Annotated[uuid.UUID, Query()], db: DB, student: Student) -> list[dict]:
    rows = db.execute(_available(db, student).where(Assignment.subject_id == subject_id)).all()
    by_topic: dict[uuid.UUID, int] = {}
    for v, _a in rows:
        by_topic[v.topic_id] = by_topic.get(v.topic_id, 0) + 1
    out = []
    for tid, n in by_topic.items():
        t = db.get(CurriculumTopic, tid)
        comp = db.get(Competency, t.competency_id) if t else None
        score = db.scalar(select(StudentCompetencyProgress.score).where(
            StudentCompetencyProgress.student_user_id == student.id,
            StudentCompetencyProgress.competency_id == (comp.id if comp else None)))
        if t and comp:
            out.append({"id": t.id, "title": t.title, "objective": t.learning_objective, "competency": comp.name,
                        "activities": n, "my_progress_percent": round(float(score) * 100) if score is not None else None})
    return sorted(out, key=lambda x: x["title"])


@router.get("/activities")
def activities(topic_id: Annotated[uuid.UUID, Query()], db: DB, student: Student) -> list[dict]:
    out = []
    for v, a in db.execute(_available(db, student).where(AssignmentVariant.topic_id == topic_id)).all():
        started = db.scalar(select(StudentAssignment.id).where(StudentAssignment.assignment_id == a.id,
                                                               StudentAssignment.student_user_id == student.id))
        n = db.scalar(select(func.count(Question.id)).where(Question.variant_id == v.id)) or 0
        out.append({"variant_id": v.id, "title": v.title, "questions": n, "already_started": started is not None})
    return out


@router.post("/start")
def start(body: StartIn, db: DB, student: Student) -> dict:
    """Crea (o recupera) la tarea de práctica voluntaria y devuelve el contenido listo para usar offline."""
    row = db.execute(_available(db, student).where(AssignmentVariant.id == body.variant_id)).first()
    if row is None:
        raise NotFoundError("Actividad no disponible")   # otro grado / otra escuela / no publicada: 404
    v, a = row
    sa = db.scalar(select(StudentAssignment).where(StudentAssignment.assignment_id == a.id,
                                                   StudentAssignment.student_user_id == student.id))
    if sa is None:
        sa = StudentAssignment(assignment_id=a.id, variant_id=v.id, student_user_id=student.id, origin="SELF", seq=next_seq(db))
        db.add(sa)
        db.commit()
        db.refresh(sa)
    return task_payload(db, sa, v, preferred_language(db, student))
