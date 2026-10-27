import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.permissions import require_roles
from app.modules.audit.service import log_access
from app.modules.automation import events
from app.modules.classrooms.service import teacher_can_access_student
from app.modules.curriculum.models import Competency
from app.modules.interventions.models import TeacherIntervention
from app.modules.learning.models import StudentCompetencyProgress
from app.modules.support_flags.models import SupportFlag
from app.modules.users.models import Role, User

router = APIRouter(prefix="/interventions", tags=["interventions"])
Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]
DB = Annotated[Session, Depends(get_db)]


class InterventionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_id: uuid.UUID
    competency_id: uuid.UUID
    strategy: str = Field(min_length=3, max_length=300)
    notes: str | None = Field(default=None, max_length=3000)
    support_flag_id: uuid.UUID | None = None


def _score(db: Session, student_id: uuid.UUID, competency_id: uuid.UUID) -> float | None:
    s = db.scalar(select(StudentCompetencyProgress.score).where(StudentCompetencyProgress.student_user_id == student_id,
                                                                StudentCompetencyProgress.competency_id == competency_id))
    return float(s) if s is not None else None


@router.post("", status_code=201)
def create(body: InterventionIn, db: DB, teacher: Teacher) -> dict:
    if not teacher_can_access_student(db, teacher.id, body.student_id):
        raise NotFoundError("Estudiante no encontrado")
    if db.get(Competency, body.competency_id) is None:
        raise NotFoundError("Competencia no encontrada")
    if body.support_flag_id is not None:
        flag = db.get(SupportFlag, body.support_flag_id)
        if flag is None or flag.student_user_id != body.student_id:
            raise NotFoundError("Alerta no encontrada")
        if flag.status == "OPEN":
            flag.status = "ACKNOWLEDGED"
    row = TeacherIntervention(teacher_id=teacher.id, student_user_id=body.student_id, competency_id=body.competency_id,
                              support_flag_id=body.support_flag_id, strategy=body.strategy.strip(), notes=body.notes,
                              score_at_creation=_score(db, body.student_id, body.competency_id))
    db.add(row)
    db.flush()
    events.emit(db, events.INTERVENTION_CREATED, {"intervention_id": str(row.id), "teacher_id": str(teacher.id),
                                                  "competency_id": str(body.competency_id)})
    db.commit()
    return {"id": row.id}


@router.get("")
def list_for_student(student_id: uuid.UUID, db: DB, teacher: Teacher) -> list[dict]:
    if not teacher_can_access_student(db, teacher.id, student_id):
        raise NotFoundError("Estudiante no encontrado")
    log_access(db, teacher, "interventions.list", "student", student_id)
    out = []
    for i in db.scalars(select(TeacherIntervention).where(TeacherIntervention.student_user_id == student_id)
                        .order_by(TeacherIntervention.created_at)):
        now = _score(db, i.student_user_id, i.competency_id)
        before = float(i.score_at_creation) if i.score_at_creation is not None else None
        out.append({"id": i.id, "competency_id": i.competency_id, "strategy": i.strategy, "notes": i.notes,
                    "created_at": i.created_at, "score_at_creation": before, "score_now": now,
                    "observed_change": round(now - before, 4) if now is not None and before is not None else None,
                    "note": "Evolución observada; no implica que la intervención sea la causa."})
    return out
