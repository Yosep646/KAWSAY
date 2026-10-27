from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.domain import adaptive
from app.modules.curriculum.models import Competency
from app.modules.learning.models import LearningAttempt, StudentCompetencyProgress
from app.modules.users.models import Role, User

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/me")
def my_progress(db: Annotated[Session, Depends(get_db)],
                student: Annotated[User, Depends(require_roles(Role.STUDENT))]) -> list[dict]:
    """Vista sencilla y positiva: solo porcentaje por competencia (sin etiquetas negativas ni estados internos)."""
    rows = db.execute(select(StudentCompetencyProgress, Competency.name).join(
        Competency, Competency.id == StudentCompetencyProgress.competency_id)
        .where(StudentCompetencyProgress.student_user_id == student.id).order_by(Competency.name))
    return [{"competency": name, "percent": round(float(p.score) * 100) if p.score is not None else None}
            for p, name in rows]


@router.get("/me/messages")
def my_messages(db: Annotated[Session, Depends(get_db)],
                student: Annotated[User, Depends(require_roles(Role.STUDENT))]) -> list[str]:
    """Mensajes de motivación SOLO si hay evidencia real (menos pistas, rachas, mejora)."""
    by_comp: dict = {}
    for a in db.scalars(select(LearningAttempt).where(LearningAttempt.student_user_id == student.id)):
        by_comp.setdefault(a.competency_id, []).append(adaptive.AttemptFact(
            str(a.id), str(a.question_id), a.attempt_number, a.is_correct, a.hints_used, a.effective_at))
    names = {c.id: c.name for c in db.scalars(select(Competency))}
    out: list[str] = []
    for cid, facts in by_comp.items():
        out += adaptive.motivation_messages(adaptive.question_results(facts), names.get(cid, "esta competencia"))
    return out
