import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.rate_limit import check_rate
from app.modules.ai.gateway import AIGateway, get_gateway
from app.modules.assignments.models import Assignment
from app.modules.audit.service import log_access
from app.modules.automation.models import DomainEvent
from app.modules.classrooms.service import teacher_can_access_student
from app.modules.tutor import service
from app.modules.users.models import Role, User

router = APIRouter(prefix="/tutor", tags=["tutor"])


class TurnIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_assignment_id: uuid.UUID
    question_id: uuid.UUID
    step: int = Field(default=0, ge=0, le=3)   # ayudas ya vistas en el cliente (la app puede estar offline)


@router.post("/turn")
def turn(body: TurnIn, db: Annotated[Session, Depends(get_db)], student: Annotated[User, Depends(require_roles(Role.STUDENT))],
         gateway: Annotated[AIGateway, Depends(get_gateway)]) -> dict:
    check_rate(f"tutor:{student.id}", 30, 60)
    return service.turn(db, gateway, student, body.student_assignment_id, body.question_id, body.step)


@router.get("/status")
def tutor_status(_: Annotated[User, Depends(require_roles(Role.STUDENT, Role.TEACHER, Role.ADMIN))],
                 gateway: Annotated[AIGateway, Depends(get_gateway)]) -> dict:
    """Diferencia un modelo CONFIGURADO de uno efectivamente probado durante una pista."""
    return {
        "ai_configured": gateway.enabled,
        "provider": gateway.provider.name if gateway.enabled else "none",
        "offline_hints_available": True,
        "model_health_verified": False,
        "message": ("Un modelo de IA está configurado. Su disponibilidad se comprueba al solicitar una pista."
                    if gateway.enabled else
                    "Tutor basado en pistas pedagógicas y reglas, sin modelo generativo configurado."),
    }


@router.get("/help-requests")
def teacher_help_requests(
    db: Annotated[Session, Depends(get_db)],
    teacher: Annotated[User, Depends(require_roles(Role.TEACHER))],
    limit: Annotated[int, Query(ge=1, le=100)] = 40,
) -> list[dict]:
    """Señales reales de apoyo solicitadas por alumnos del docente; no son diagnósticos."""
    rows = db.scalars(
        select(DomainEvent).where(DomainEvent.type == "tutor.help.requested")
        .order_by(DomainEvent.created_at.desc()).limit(200)
    )
    out = []
    for ev in rows:
        payload = ev.payload if isinstance(ev.payload, dict) else {}
        if payload.get("teacher_id") != str(teacher.id):
            continue
        try:
            sid = uuid.UUID(payload["student_id"])
            aid = uuid.UUID(payload["assignment_id"])
        except (KeyError, ValueError, TypeError):
            continue
        if not teacher_can_access_student(db, teacher.id, sid):
            continue
        student = db.get(User, sid)
        assignment = db.get(Assignment, aid)
        if student is None or assignment is None:
            continue
        out.append({
            "id": ev.id, "student": student.display_name,
            "assignment_title": assignment.title,
            "requested_at": ev.created_at,
            "reason": "El estudiante solicitó al menos dos niveles de ayuda en un ejercicio.",
            "source": "TUTOR_RULES",
            "requires_teacher_decision": True,
        })
        if len(out) >= limit:
            break
    log_access(db, teacher, "tutor.help_requests.read", "tutor")
    return out
