import uuid

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from datetime import UTC, datetime
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


def eligible_students(db: Session, teacher_id: uuid.UUID, classroom_id: uuid.UUID) -> list[dict]:
    """Solo alumnos ya vinculados con aulas del mismo docente y la misma escuela.

    No expone el directorio completo de escolares ni datos de otras instituciones.
    """
    room = get_teacher_classroom(db, teacher_id, classroom_id)
    rows = db.execute(
        select(User.id, User.display_name, Grade.number, Classroom.id, Classroom.name, Classroom.academic_year)
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .join(Grade, Grade.id == StudentProfile.grade_id)
        .join(ClassroomStudent, ClassroomStudent.student_user_id == User.id)
        .join(Classroom, Classroom.id == ClassroomStudent.classroom_id)
        .join(ClassroomTeacher, ClassroomTeacher.classroom_id == Classroom.id)
        .where(
            ClassroomTeacher.teacher_user_id == teacher_id,
            StudentProfile.school_id == room.school_id,
            User.role == "STUDENT",
            User.is_active.is_(True),
            User.deleted_at.is_(None),
            Classroom.deleted_at.is_(None),
            ClassroomStudent.left_at.is_(None),
            Classroom.id != room.id,
        ).order_by(User.display_name)
    )
    enrolled_in_target_year = set(db.scalars(
        select(ClassroomStudent.student_user_id)
        .join(Classroom, Classroom.id == ClassroomStudent.classroom_id)
        .where(Classroom.school_id == room.school_id,
               Classroom.academic_year == room.academic_year,
               Classroom.deleted_at.is_(None),
               ClassroomStudent.left_at.is_(None))
    ))
    candidates = {}
    for sid, display_name, grade, source_id, source_name, source_year in rows:
        if source_year == room.academic_year or sid in enrolled_in_target_year:
            continue  # Una matrícula activa por año y sin traslados automáticos.
        candidates[str(sid)] = {
            "id": sid, "display_name": display_name, "grade_number": grade,
            "previous_classroom": source_name, "previous_academic_year": source_year,
        }
    return list(candidates.values())


def enroll_existing_student(db: Session, teacher: User, classroom_id: uuid.UUID,
                            student_id: uuid.UUID) -> dict:
    """Nueva matrícula en año distinto, preservando cuenta, grado, avance e historial."""
    room = get_teacher_classroom(db, teacher.id, classroom_id)
    profile = db.get(StudentProfile, student_id)
    user = db.get(User, student_id)
    if (profile is None or user is None or profile.school_id != room.school_id
            or user.role != "STUDENT" or not user.is_active or user.deleted_at is not None):
        raise NotFoundError("Estudiante no disponible para esta matrícula")

    # Se exige relación docente previa; no basta conocer un UUID de un escolar.
    accessible_before = db.scalar(select(exists().where(
        ClassroomTeacher.teacher_user_id == teacher.id,
        ClassroomTeacher.classroom_id == ClassroomStudent.classroom_id,
        ClassroomStudent.student_user_id == student_id,
        ClassroomStudent.left_at.is_(None),
    )))
    if not accessible_before:
        raise NotFoundError("Estudiante no disponible para esta matrícula")

    current = db.scalars(
        select(ClassroomStudent).join(Classroom, Classroom.id == ClassroomStudent.classroom_id)
        .where(ClassroomStudent.student_user_id == student_id,
               ClassroomStudent.left_at.is_(None),
               Classroom.deleted_at.is_(None),
               Classroom.school_id == room.school_id,
               Classroom.academic_year == room.academic_year)
    )
    if any(True for _ in current):
        raise ConflictError("El estudiante ya tiene una matrícula activa en ese año escolar")

    existing = db.get(ClassroomStudent, (room.id, student_id))
    if existing is not None:
        existing.left_at = None
        existing.joined_at = datetime.now(UTC)
    else:
        db.add(ClassroomStudent(classroom_id=room.id, student_user_id=student_id))
    db.flush()
    from app.modules.assignments.service import assign_published_to_new_student
    assign_published_to_new_student(db, room, student_id)
    db.commit()
    return {"student_id": student_id, "classroom_id": room.id, "status": "ENROLLED",
            "grade_id": profile.grade_id, "academic_year": room.academic_year}
