from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import require_roles
from app.modules.audit.service import log_access
from app.modules.automation.dispatch import dispatch_pending
from app.modules.automation.models import DomainEvent
from app.modules.users.models import Role, User

router = APIRouter(prefix="/automation", tags=["automation"])
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]
DB = Annotated[Session, Depends(get_db)]


@router.get("/events")
def list_events(db: DB, _: Admin, status: str | None = None, limit: Annotated[int, Query(ge=1, le=200)] = 50) -> list[dict]:
    q = select(DomainEvent).order_by(DomainEvent.created_at.desc()).limit(limit)
    if status:
        q = q.where(DomainEvent.status == status)
    return [{"id": e.id, "type": e.type, "status": e.status, "attempts": e.attempts, "last_error": e.last_error,
             "created_at": e.created_at} for e in db.scalars(q)]


@router.post("/dispatch")
def dispatch(db: DB, _: Admin) -> dict:
    return dispatch_pending(db)


@router.post("/events/{event_id}/retry")
def retry_event(event_id: UUID, db: DB, admin: Admin) -> dict:
    event = db.get(DomainEvent, event_id)
    if event is None:
        raise NotFoundError("Evento no encontrado")
    if event.status != "FAILED":
        raise ConflictError("Solo se pueden reintentar eventos fallidos")
    event.status = "PENDING"
    event.attempts = 0
    event.last_error = None
    event.next_attempt_at = datetime.now(UTC)
    log_access(db, admin, "automation.event.retry", "domain_event", event.id)
    return {"id": event.id, "status": event.status}
