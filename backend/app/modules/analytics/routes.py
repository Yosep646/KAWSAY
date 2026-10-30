import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.permissions import require_roles
from app.domain import adaptive
from app.modules.assignments.models import Assignment
from app.modules.audit.service import log_access
from app.modules.classrooms.models import ClassroomStudent
from app.modules.classrooms.service import classroom_students, get_teacher_classroom, teacher_can_access_student
from app.modules.curriculum.models import Competency, Grade
from app.modules.learning.models import LearningAttempt, StudentCompetencyProgress
from app.modules.students.models import StudentProfile
from app.modules.support_flags.models import SupportFlag
from app.modules.users.models import Role, User

router = APIRouter(prefix="/analytics", tags=["analytics"])
Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]
DB = Annotated[Session, Depends(get_db)]


@router.get("/classrooms/{classroom_id}/summary")
def classroom_summary(classroom_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    """Solo datos reales calculados desde la BD. Sin evidencia => 0/vacío, nunca cifras inventadas."""
    room = get_teacher_classroom(db, teacher.id, classroom_id)
    students = classroom_students(db, room.id)
    ids = [s["id"] for s in students]
    by_grade: dict[str, int] = {}
    for s in students:
        k = f"{s['grade_number']}.º {s['grade_level']}"
        by_grade[k] = by_grade.get(k, 0) + 1
    attempts = (db.scalar(select(func.count(LearningAttempt.id)).where(LearningAttempt.student_user_id.in_(ids)))
                if ids else 0)
    active_students = (db.scalar(select(func.count(func.distinct(LearningAttempt.student_user_id)))
                                 .where(LearningAttempt.student_user_id.in_(ids))) if ids else 0)
    open_flags = (db.scalar(select(func.count(SupportFlag.id)).where(
        SupportFlag.student_user_id.in_(ids), SupportFlag.status.in_(("OPEN", "ACKNOWLEDGED")))) if ids else 0)
    published = db.scalar(select(func.count(Assignment.id)).where(Assignment.classroom_id == room.id,
                                                                  Assignment.status == "PUBLISHED"))
    return {"classroom": {"id": room.id, "name": room.name, "academic_year": room.academic_year},
            "students_total": len(students), "students_by_grade": by_grade, "published_assignments": published,
            "attempts_total": attempts or 0, "students_with_activity": active_students or 0,
            "open_support_flags": open_flags or 0}


@router.get("/classrooms/{classroom_id}/students/{student_id}/progress")
def student_progress(classroom_id: uuid.UUID, student_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    room = get_teacher_classroom(db, teacher.id, classroom_id)
    log_access(db, teacher, "analytics.student_progress", "student", student_id)
    in_room = db.scalar(select(ClassroomStudent.student_user_id).where(
        ClassroomStudent.classroom_id == room.id, ClassroomStudent.student_user_id == student_id,
        ClassroomStudent.left_at.is_(None)))
    if in_room is None or not teacher_can_access_student(db, teacher.id, student_id):
        raise NotFoundError("Estudiante no encontrado")
    rows = db.execute(select(StudentCompetencyProgress, Competency.name).join(
        Competency, Competency.id == StudentCompetencyProgress.competency_id)
        .where(StudentCompetencyProgress.student_user_id == student_id).order_by(Competency.name))
    return {"student_id": student_id, "competencies": [
        {"competency_id": p.competency_id, "name": name, "score": float(p.score) if p.score is not None else None,
         "evidence_count": p.evidence_count, "state": p.state, "method_version": p.method_version,
         "difficulty_recommendation": {**adaptive.difficulty_recommendation(
             float(p.score) if p.score is not None else None, p.evidence_count),
             "source": "RULES", "method_version": adaptive.METHOD_VERSION,
             "requires_teacher_decision": True},
         "note": None if p.score is not None else "Sin evidencia suficiente"} for p, name in rows]}


@router.get("/classrooms/{classroom_id}/strengths")
def strengths(classroom_id: uuid.UUID, db: DB, teacher: Teacher) -> list[dict]:
    """Fortalezas observables (mejora, menos pistas, rachas, dominio creciente), calculadas de intentos reales."""
    room = get_teacher_classroom(db, teacher.id, classroom_id)
    log_access(db, teacher, "analytics.strengths", "classroom", room.id)
    students = {s["id"]: s for s in classroom_students(db, room.id)}
    if not students:
        return []
    by_key: dict[tuple, list] = {}
    for a in db.scalars(select(LearningAttempt).where(LearningAttempt.student_user_id.in_(list(students)))):
        by_key.setdefault((a.student_user_id, a.competency_id), []).append(
            adaptive.AttemptFact(str(a.id), str(a.question_id), a.attempt_number, a.is_correct, a.hints_used, a.effective_at))
    names = {c.id: c.name for c in db.scalars(select(Competency))}
    out = []
    for (sid, cid), facts in by_key.items():
        found = adaptive.detect_strengths(adaptive.question_results(facts))
        if found:
            st = students[sid]
            out.append({"student": {"id": sid, "display_name": st["display_name"],
                                    "grade": f"{st['grade_number']}.º {st['grade_level']}"},
                        "competency": {"id": cid, "name": names.get(cid)}, "strengths": found})
    return out


_ = (Grade, StudentProfile)


@router.get("/classrooms/{classroom_id}/forecast")
def forecast(classroom_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    """Pronóstico ML OPCIONAL (solo con un modelo aprobado). Sin modelo: available=false y el sistema sigue con reglas."""
    from app.modules.forecast.service import forecast_for_students
    room = get_teacher_classroom(db, teacher.id, classroom_id)
    log_access(db, teacher, "analytics.forecast", "classroom", room.id)
    students = {s["id"]: s for s in classroom_students(db, room.id)}
    return forecast_for_students(db, students) if students else {"available": False, "reason": "El aula no tiene estudiantes.", "items": []}
