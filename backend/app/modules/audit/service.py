import uuid

from sqlalchemy.orm import Session

from app.core.logging import request_id_ctx
from app.modules.audit.models import AuditLog
from app.modules.users.models import User


def log_access(db: Session, actor: User, action: str, target_type: str, target_id: uuid.UUID | None = None) -> None:
    rid = request_id_ctx.get()
    db.add(AuditLog(actor_user_id=actor.id, action=action, target_type=target_type, target_id=target_id,
                    request_id=None if rid == "-" else rid))
    db.commit()
