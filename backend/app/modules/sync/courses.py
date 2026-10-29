"""Catálogo de cursos por estudiante, derivado únicamente de la planificación ACTIVE.

Un curso es un área curricular ofrecida al grado del estudiante en su aula.
No es una actividad ni se inventa a partir de tareas descargadas.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.classrooms.models import Classroom, ClassroomStudent
from app.modules.curriculum.models import CurriculumFramework, Subject
from app.modules.planning.models import CurriculumUnit
from app.modules.planning.service import active_versions_for_school_year
from app.modules.students.models import StudentProfile


def student_courses(db: Session, student_id: uuid.UUID) -> list[dict]:
    profile = db.get(StudentProfile, student_id)
    if profile is None:
        return []
    rooms = db.scalars(
        select(Classroom)
        .join(ClassroomStudent, ClassroomStudent.classroom_id == Classroom.id)
        .where(
            ClassroomStudent.student_user_id == student_id,
            ClassroomStudent.left_at.is_(None),
            Classroom.deleted_at.is_(None),
            Classroom.school_id == profile.school_id,
        )
        .order_by(Classroom.academic_year, Classroom.name)
    )
    result: list[dict] = []
    seen: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for room in rooms:
        versions = active_versions_for_school_year(db, room.school_id, room.academic_year)
        if not versions:
            continue
        units = db.scalars(
            select(CurriculumUnit)
            .where(
                CurriculumUnit.version_id.in_([v.id for v in versions]),
                CurriculumUnit.grade_id == profile.grade_id,
            )
            .order_by(CurriculumUnit.subject_id)
        )
        for unit in units:
            key = (room.id, unit.subject_id)
            if key in seen:
                continue
            subject = db.get(Subject, unit.subject_id)
            if subject is None:
                continue
            framework = db.get(CurriculumFramework, subject.framework_id)
            seen.add(key)
            result.append({
                "id": f"{room.id}:{subject.id}",
                "subject_id": str(subject.id),
                "name": subject.name,
                "classroom_id": str(room.id),
                "classroom_name": room.name,
                "academic_year": room.academic_year,
                "grade_id": profile.grade_id,
                "is_demo": bool(framework.is_demo) if framework else False,
            })
    return sorted(result, key=lambda c: (c["name"].casefold(), c["classroom_name"].casefold()))
