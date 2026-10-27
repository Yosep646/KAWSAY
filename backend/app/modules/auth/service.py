import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    burn_verification_time,
    create_access_token,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.modules.auth.models import RefreshToken
from app.modules.users.models import Role, User

log = logging.getLogger("kawsay.security")
_INVALID = "Credenciales inválidas"


def _now() -> datetime:
    return datetime.now(UTC)


def _fail(identifier: str, reason: str) -> None:
    # El identificador se registra solo como huella corta (permite correlacionar ataques sin guardar datos personales)
    log.warning("login_failed", extra={"extra_fields": {"subject": hashlib.sha256(identifier.encode()).hexdigest()[:12], "reason": reason}})


def _check_secret(db: Session, user: User | None, secret: str, identifier: str = "") -> User:
    if user is None:
        burn_verification_time(secret)
        _fail(identifier, "unknown_user")
        raise UnauthorizedError(_INVALID)
    s = get_settings()
    now = _now()
    if user.locked_until and user.locked_until > now:
        _fail(identifier, "locked")
        raise UnauthorizedError(_INVALID)  # mismo mensaje: no revelar bloqueo/existencia
    if not user.is_active or not verify_password(user.password_hash, secret):
        user.failed_login_count += 1
        if user.failed_login_count >= s.max_failed_logins:
            user.locked_until = now + timedelta(minutes=s.lockout_minutes)
            user.failed_login_count = 0
            log.warning("account_locked", extra={"extra_fields": {"subject": hashlib.sha256(identifier.encode()).hexdigest()[:12]}})
        db.commit()
        _fail(identifier, "bad_credentials")
        raise UnauthorizedError(_INVALID)
    user.failed_login_count = 0
    user.locked_until = None
    return user


def _issue_tokens(db: Session, user: User, device_id: uuid.UUID | None,
                  family_id: uuid.UUID | None = None) -> dict:
    s = get_settings()
    raw = new_refresh_token()
    row = RefreshToken(
        user_id=user.id, family_id=family_id or uuid.uuid4(), token_hash=hash_refresh_token(raw),
        device_id=device_id, expires_at=_now() + timedelta(days=s.refresh_token_expire_days),
    )
    db.add(row)
    db.flush()
    access, ttl = create_access_token(user.id, user.role)
    return {"access_token": access, "refresh_token": raw, "expires_in": ttl,
            "user": {"id": user.id, "role": user.role, "display_name": user.display_name},
            "_row": row}


def _public(tokens: dict) -> dict:
    return {k: v for k, v in tokens.items() if not k.startswith("_")}


def login_with_password(db: Session, email: str, password: str, device_id: uuid.UUID | None) -> dict:
    user = db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None),
                                        User.role != Role.STUDENT))
    user = _check_secret(db, user, password, email)
    tokens = _issue_tokens(db, user, device_id)
    db.commit()
    return _public(tokens)


def login_student(db: Session, login_code: str, pin: str, device_id: uuid.UUID) -> dict:
    user = db.scalar(select(User).where(User.login_code == login_code.upper(), User.deleted_at.is_(None),
                                        User.role == Role.STUDENT))
    user = _check_secret(db, user, pin, login_code)
    tokens = _issue_tokens(db, user, device_id)
    db.commit()
    return _public(tokens)


def revoke_family(db: Session, family_id: uuid.UUID) -> None:
    db.execute(update(RefreshToken).where(RefreshToken.family_id == family_id,
                                          RefreshToken.revoked_at.is_(None)).values(revoked_at=_now()))


def revoke_all_for_user(db: Session, user_id: uuid.UUID) -> None:
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user_id,
                                          RefreshToken.revoked_at.is_(None)).values(revoked_at=_now()))


def refresh(db: Session, raw_token: str) -> dict:
    tok = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token)))
    if tok is None:
        raise UnauthorizedError("Token inválido o expirado")
    now = _now()
    if tok.revoked_at is not None:
        # Reutilización de un token ya rotado: posible robo -> se invalida toda la familia.
        revoke_family(db, tok.family_id)
        db.commit()
        raise UnauthorizedError("Token inválido o expirado")
    if tok.expires_at <= now:
        raise UnauthorizedError("Token inválido o expirado")
    user = db.get(User, tok.user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise UnauthorizedError("Token inválido o expirado")
    tokens = _issue_tokens(db, user, tok.device_id, family_id=tok.family_id)
    tok.revoked_at = now
    tok.replaced_by = tokens["_row"].id
    db.commit()
    return _public(tokens)


def logout(db: Session, raw_token: str) -> None:
    tok = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token)))
    if tok is not None:
        revoke_family(db, tok.family_id)
        db.commit()


def change_password(db: Session, user: User, current: str, new: str) -> dict:
    """Exige la contraseña actual, cumple la política, y CIERRA todas las demás sesiones."""
    from app.core.password_policy import check_password_policy
    from app.core.security import hash_password
    if not verify_password(user.password_hash, current):
        log.warning("change_password_failed", extra={"extra_fields": {"user": str(user.id)}})
        raise UnauthorizedError(_INVALID)
    if verify_password(user.password_hash, new):
        from app.core.password_policy import WeakPassword
        raise WeakPassword("La nueva contraseña debe ser distinta de la actual")
    check_password_policy(new, user.email, user.display_name)
    user.password_hash = hash_password(new)
    revoke_all_for_user(db, user.id)
    tokens = _issue_tokens(db, user, None)
    db.commit()
    return _public(tokens)
