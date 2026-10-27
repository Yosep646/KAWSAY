import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.permissions import require_roles
from app.modules.audit.service import log_access
from app.modules.classrooms.models import ClassroomStudent, ClassroomTeacher
from app.modules.classrooms.service import get_teacher_classroom, teacher_can_access_student
from app.modules.curriculum.models import Competency, Grade
from app.modules.students.models import StudentProfile
from app.modules.support_flags.models import SupportFlag
from app.modules.users.models import Role, User

router = APIRouter(prefix="/support-flags", tags=["support-flags"])
Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]
DB = Annotated[Session, Depends(get_db)]

MESSAGES = {"GUIDED_ACTIVITY": "Se recomienda una actividad guiada y revisar el progreso del estudiante en esta competencia."}


def explain(flag: SupportFlag, student: str, competency: str) -> str:
    e = flag.evidence
    topics = ", ".join(e.get("topics", [])) or "los ejercicios recientes"
    return (f"Se recomienda revisar el progreso de {student} en {competency} ({topics}). "
            f"Evidencia: {e['difficult']} de los últimos {e['window']} ejercicios presentan dificultad; "
            f"{e['hints_total']} pistas utilizadas; {e['wrong_attempts_total']} intentos incorrectos; "
            f"patrón observado en {e['distinct_days']} día(s). El docente decide qué hacer.")


def flag_out(db: Session, f: SupportFlag) -> dict:
    student = db.get(User, f.student_user_id)
    prof = db.scalar(select(StudentProfile).where(StudentProfile.user_id == f.student_user_id))
    grade = db.get(Grade, prof.grade_id) if prof else None
    comp = db.get(Competency, f.competency_id)
    name, cname = (student.display_name if student else "?"), (comp.name if comp else "?")
    return {"id": f.id, "status": f.status, "student": {"id": f.student_user_id, "display_name": name,
                                                           "grade": f"{grade.number}.º {grade.level}" if grade else None},
            "competency": {"id": f.competency_id, "name": cname}, "rule_id": f.rule_id, "rule_version": f.rule_version,
            "evidence": f.evidence, "recommendation": MESSAGES.get(f.recommendation_code),
            "message": explain(f, name, cname), "created_at": f.created_at, "updated_at": f.updated_at}


class FlagPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ACKNOWLEDGED", "RESOLVED", "DISMISSED"]


@router.get("")
def list_flags(db: DB, teacher: Teacher, classroom_id: uuid.UUID | None = None,
               status: Literal["OPEN", "ACKNOWLEDGED", "RESOLVED", "DISMISSED"] | None = None,
               limit: Annotated[int, Query(ge=1, le=100)] = 50) -> list[dict]:
    log_access(db, teacher, "support_flags.list", "classroom", classroom_id)
    q = (select(SupportFlag).join(ClassroomStudent, ClassroomStudent.student_user_id == SupportFlag.student_user_id)
         .join(ClassroomTeacher, ClassroomTeacher.classroom_id == ClassroomStudent.classroom_id)
         .where(ClassroomTeacher.teacher_user_id == teacher.id, ClassroomStudent.left_at.is_(None)))
    if classroom_id:
        get_teacher_classroom(db, teacher.id, classroom_id)  # 404 si no es su aula
        q = q.where(ClassroomStudent.classroom_id == classroom_id)
    if status:
        q = q.where(SupportFlag.status == status)
    flags = db.scalars(q.distinct().order_by(SupportFlag.updated_at.desc()).limit(limit))
    return [flag_out(db, f) for f in flags]


@router.patch("/{flag_id}")
def patch_flag(flag_id: uuid.UUID, body: FlagPatch, db: DB, teacher: Teacher) -> dict:
    f = db.get(SupportFlag, flag_id)
    if f is None or not teacher_can_access_student(db, teacher.id, f.student_user_id):
        raise NotFoundError("Alerta no encontrada")
    f.status = body.status
    f.resolved_at = datetime.now(UTC) if body.status in ("RESOLVED", "DISMISSED") else None
    db.commit()
    return flag_out(db, f)
