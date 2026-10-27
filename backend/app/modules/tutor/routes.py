import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.rate_limit import check_rate
from app.modules.ai.gateway import AIGateway, get_gateway
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
