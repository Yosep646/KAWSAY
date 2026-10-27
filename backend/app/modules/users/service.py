import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.password_policy import check_password_policy
from app.core.security import hash_password
from app.modules.schools.models import School
from app.modules.teachers.models import TeacherProfile
from app.modules.users.models import Role, User
from app.modules.users.schemas import UserCreate


def create_staff_user(db: Session, data: UserCreate) -> User:
    check_password_policy(data.password, data.email, data.display_name)
    if data.school_id is not None and db.scalar(
            select(School.id).where(School.id == data.school_id, School.deleted_at.is_(None))) is None:
        raise NotFoundError("Escuela no encontrada")
    user = User(email=data.email.lower(), password_hash=hash_password(data.password), role=data.role,
                display_name=data.display_name.strip())
    db.add(user)
    try:
        db.flush()
        if data.role == Role.TEACHER:
            db.add(TeacherProfile(user_id=user.id, school_id=data.school_id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("El correo ya está registrado") from exc
    return user


def list_users(db: Session, limit: int, offset: int) -> list[User]:
    return list(db.scalars(select(User).where(User.deleted_at.is_(None))
                           .order_by(User.created_at, User.id).limit(limit).offset(offset)))


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise NotFoundError("Usuario no encontrado")
    return user


def set_active(db: Session, admin: User, user_id: uuid.UUID, active: bool) -> User:
    from app.core.exceptions import ConflictError as _Conflict
    from app.modules.auth.service import revoke_all_for_user
    if user_id == admin.id:
        raise _Conflict("No puedes desactivar tu propia cuenta")
    user = get_user(db, user_id)
    user.is_active = active
    if not active:
        revoke_all_for_user(db, user.id)   # la desactivación cierra todas sus sesiones de inmediato
    db.commit()
    return user
