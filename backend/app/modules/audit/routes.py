import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.modules.audit.models import AuditLog
from app.modules.users.models import Role, User

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("")
def list_audit(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_roles(Role.ADMIN))],
               actor_id: uuid.UUID | None = None, limit: Annotated[int, Query(ge=1, le=200)] = 50) -> list[dict]:
    q = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if actor_id:
        q = q.where(AuditLog.actor_user_id == actor_id)
    return [{"id": a.id, "actor_user_id": a.actor_user_id, "action": a.action, "target_type": a.target_type,
             "target_id": a.target_id, "request_id": a.request_id, "created_at": a.created_at} for a in db.scalars(q)]
