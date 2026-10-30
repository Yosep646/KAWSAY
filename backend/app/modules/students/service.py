import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.security import generate_login_code, generate_pin, hash_password
from app.modules.assignments.service import assign_published_to_new_student
from app.modules.auth.service import revoke_all_for_user
from app.modules.classrooms import service as classrooms
from app.modules.classrooms.models import ClassroomStudent
from app.modules.curriculum.models import Grade
from app.modules.students.models import StudentProfile
from app.modules.users.models import Role, User


def create_student(db: Session, teacher: User, display_name: str, grade_id: int,
                   classroom_id: uuid.UUID) -> tuple[User, str]:
    room = classrooms.get_teacher_classroom(db, teacher.id, classroom_id)
    if db.get(Grade, grade_id) is None:
        raise NotFoundError("Grado no encontrado")
    pin = generate_pin()
    for _ in range(5):  # colisión de login_code: reintentar
        user = User(login_code=generate_login_code(), password_hash=hash_password(pin), role=Role.STUDENT,
                    display_name=display_name.strip())
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            room = classrooms.get_teacher_classroom(db, teacher.id, classroom_id)
            continue
        db.add(StudentProfile(user_id=user.id, school_id=room.school_id, grade_id=grade_id))
        db.add(ClassroomStudent(classroom_id=room.id, student_user_id=user.id))
        db.flush()
        assign_published_to_new_student(db, room, user.id)
        db.commit()
        return user, pin
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
    pin = generate_pin()
    user.password_hash = hash_password(pin)
    user.failed_login_count = 0
    user.locked_until = None
    revoke_all_for_user(db, user.id)
    db.commit()
    return pin
