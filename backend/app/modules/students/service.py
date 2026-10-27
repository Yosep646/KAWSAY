import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.password_policy import check_password_policy
from app.core.security import generate_login_code, generate_pin, hash_password
from app.modules.auth.service import revoke_all_for_user
from app.modules.assignments.service import assign_published_to_new_student
from app.modules.classrooms import service as classrooms
from app.modules.classrooms.models import ClassroomStudent
from app.modules.curriculum.models import Grade
from app.modules.students.email_models import StudentEmailLogin
from app.modules.students.models import StudentProfile
from app.modules.users.models import Role, User


def create_student(
    db: Session, teacher: User, display_name: str, grade_id: int,
    classroom_id: uuid.UUID, email: str | None = None, password: str | None = None
) -> tuple[User, str | None]:
    """El docente asignado crea estudiantes por correo/clave o por código/PIN heredado.

    El modo correo mantiene el login_code interno para no invalidar las relaciones
    existentes. El correo sólo existe en student_email_logins (datos mínimos).
    """
    room = classrooms.get_teacher_classroom(db, teacher.id, classroom_id)
    if db.get(Grade, grade_id) is None:
        raise NotFoundError("Grado no encontrado")
    if bool(email) != bool(password):
        raise ConflictError("Correo y contraseña deben indicarse juntos")
    normalized_email = email.strip().lower() if email else None
    if normalized_email:
        check_password_policy(password or "", normalized_email, display_name)
        if (db.scalar(select(StudentEmailLogin.user_id).where(StudentEmailLogin.email == normalized_email))
                or db.scalar(select(User.id).where(User.email == normalized_email, User.deleted_at.is_(None)))):
            raise ConflictError("El correo ya está registrado")
    pin = None if normalized_email else generate_pin()
    for _ in range(5):  # colisión del código interno: reintentar
        user = User(login_code=generate_login_code(), password_hash=hash_password(password if normalized_email else (pin or "")),
                    role=Role.STUDENT, display_name=display_name.strip())
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            room = classrooms.get_teacher_classroom(db, teacher.id, classroom_id)
            continue
        try:
            if normalized_email:
                db.add(StudentEmailLogin(user_id=user.id, email=normalized_email))
            db.add(StudentProfile(user_id=user.id, school_id=room.school_id, grade_id=grade_id))
            db.add(ClassroomStudent(classroom_id=room.id, student_user_id=user.id))
            db.flush()
            assign_published_to_new_student(db, room, user.id)
            db.commit()
            return user, pin
        except IntegrityError as exc:
            db.rollback()
            raise ConflictError("El correo ya está registrado") from exc
    raise RuntimeError("No se pudo generar un código único")


def get_accessible_student(db: Session, teacher: User, student_id: uuid.UUID) -> tuple[User, StudentProfile]:
    if not classrooms.teacher_can_access_student(db, teacher.id, student_id):
        raise NotFoundError("Estudiante no encontrado")  # 404: no revelar existencia
    user = db.get(User, student_id)
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == student_id))
    if user is None or profile is None or user.deleted_at is not None:
        raise NotFoundError("Estudiante no encontrado")
    return user, profile


def reset_pin(db: Session, teacher: User, student_id: uuid.UUID) -> str:
    user, _ = get_accessible_student(db, teacher, student_id)
    if db.get(StudentEmailLogin, user.id):
        raise ConflictError("Este estudiante usa correo y contraseña; cambia su contraseña en lugar del PIN")
    pin = generate_pin()
    user.password_hash = hash_password(pin)
    user.failed_login_count = 0
    user.locked_until = None
    revoke_all_for_user(db, user.id)
    db.commit()
    return pin


def reset_student_password(db: Session, teacher: User, student_id: uuid.UUID, password: str) -> None:
    """Permite restablecer credenciales del estudiante SOLO a su docente."""
    user, _ = get_accessible_student(db, teacher, student_id)
    entry = db.get(StudentEmailLogin, user.id)
    if entry is None:
        raise ConflictError("El estudiante usa código y PIN, no correo electrónico")
    check_password_policy(password, entry.email, user.display_name)
    user.password_hash = hash_password(password)
    user.failed_login_count = 0
    user.locked_until = None
    revoke_all_for_user(db, user.id)
    db.commit()
