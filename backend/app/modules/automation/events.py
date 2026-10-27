from sqlalchemy.orm import Session

from app.modules.automation.models import DomainEvent

# Eventos de dominio (datos mínimos: ids y conteos; sin nombres de estudiantes)
SUPPORT_FLAG_CREATED = "student.support_flag.created"
INTERVENTION_CREATED = "teacher.intervention.created"
ASSIGNMENT_PUBLISHED = "assignment.published"
SYNC_COMPLETED = "sync.completed"


def emit(db: Session, event_type: str, payload: dict) -> None:
    """Se guarda en la MISMA transacción que el cambio de dominio (outbox transaccional)."""
    db.add(DomainEvent(type=event_type, payload=payload))
