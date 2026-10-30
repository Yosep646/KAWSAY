import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.modules.auth.models import RefreshToken
from app.modules.users.models import Role, User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if creds is None:
        raise UnauthorizedError("Autenticación requerida")
    claims = decode_access_token(creds.credentials)
    try:
        uid = uuid.UUID(claims["sub"])
        family_id = uuid.UUID(claims["sid"])
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise UnauthorizedError("Token inválido o expirado") from exc
    user = db.get(User, uid)
    # El rol SIEMPRE sale de la BD, no del token (cambios de rol/desactivación efectivos de inmediato).
    if user is None or not user.is_active or user.deleted_at is not None:
        raise UnauthorizedError("Token inválido o expirado")
    # A rotated refresh keeps its family alive. Logout, PIN reset and replay
    # revoke that family, including access tokens that have not expired yet.
    active_session = db.scalar(select(RefreshToken.id).where(
        RefreshToken.family_id == family_id, RefreshToken.user_id == uid,
        RefreshToken.revoked_at.is_(None), RefreshToken.expires_at > datetime.now(UTC)).limit(1))
    if active_session is None:
        raise UnauthorizedError("Token inválido o expirado")
    return user


def require_roles(*roles: Role) -> Callable[[User], User]:
    allowed = {r.value for r in roles}

    def dep(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise ForbiddenError("No tienes permiso para esta acción")
        return user

    return dep
