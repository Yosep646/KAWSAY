import uuid

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.classrooms.models import Classroom, ClassroomStudent, ClassroomTeacher
from app.modules.curriculum.models import Grade
from app.modules.students.models import StudentProfile
from app.modules.teachers.models import TeacherProfile
from app.modules.users.models import User


def teacher_school_id(db: Session, teacher_id: uuid.UUID) -> uuid.UUID:
    sid = db.scalar(select(TeacherProfile.school_id).where(TeacherProfile.user_id == teacher_id))
    if sid is None:
        raise NotFoundError("Perfil docente no encontrado")
    return sid


def create_classroom(db: Session, teacher: User, name: str, academic_year: int) -> Classroom:
    room = Classroom(school_id=teacher_school_id(db, teacher.id), name=name.strip(),
                     academic_year=academic_year)
    db.add(room)
    try:
        db.flush()
        db.add(ClassroomTeacher(classroom_id=room.id, teacher_user_id=teacher.id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Ya existe un aula con ese nombre en ese año") from exc
    return room


def list_teacher_classrooms(db: Session, teacher_id: uuid.UUID) -> list[Classroom]:
    return list(db.scalars(
        select(Classroom).join(ClassroomTeacher, ClassroomTeacher.classroom_id == Classroom.id)
        .where(ClassroomTeacher.teacher_user_id == teacher_id, Classroom.deleted_at.is_(None))
        .order_by(Classroom.academic_year.desc(), Classroom.name)))


def get_teacher_classroom(db: Session, teacher_id: uuid.UUID, classroom_id: uuid.UUID) -> Classroom:
    """Ownership: si el aula no es del docente responde 404 (no revela existencia)."""
    room = db.scalar(select(Classroom).join(
        ClassroomTeacher, ClassroomTeacher.classroom_id == Classroom.id).where(
        Classroom.id == classroom_id, ClassroomTeacher.teacher_user_id == teacher_id,
        Classroom.deleted_at.is_(None)))
    if room is None:
        raise NotFoundError("Aula no encontrada")
    return room


def classroom_students(db: Session, classroom_id: uuid.UUID) -> list[dict]:
    rows = db.execute(
        select(User.id, User.display_name, Grade.id, Grade.level, Grade.number)
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .join(Grade, Grade.id == StudentProfile.grade_id)
        .join(ClassroomStudent, ClassroomStudent.student_user_id == User.id)
        .where(ClassroomStudent.classroom_id == classroom_id, ClassroomStudent.left_at.is_(None),
               User.deleted_at.is_(None))
        .order_by(Grade.level, Grade.number, User.display_name))
    return [{"id": r[0], "display_name": r[1], "grade_id": r[2], "grade_level": r[3], "grade_number": r[4]}
            for r in rows]


def teacher_can_access_student(db: Session, teacher_id: uuid.UUID, student_id: uuid.UUID) -> bool:
    return bool(db.scalar(select(exists().where(
        ClassroomTeacher.teacher_user_id == teacher_id,
        ClassroomTeacher.classroom_id == ClassroomStudent.classroom_id,
        ClassroomStudent.student_user_id == student_id,
        ClassroomStudent.left_at.is_(None)))))
