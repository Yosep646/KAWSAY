import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.assignments.models import Assignment, AssignmentVariant, Counter, Question, StudentAssignment
from app.modules.automation import events
from app.modules.classrooms.models import Classroom, ClassroomStudent
from app.modules.classrooms.service import get_teacher_classroom
from app.modules.languages.models import VariantTranslation
from app.modules.planning.models import CurriculumTopic, CurriculumUnit
from app.modules.planning.service import active_versions_for_school_year
from app.modules.students.models import StudentProfile
from app.modules.users.models import User


def next_seq(db: Session) -> int:
    """Siguiente valor del cursor de sync. Seguro porque toda escritura usa BEGIN IMMEDIATE (un solo escritor)."""
    db.execute(update(Counter).where(Counter.name == "sa_seq").values(value=Counter.value + 1))
    return int(db.scalar(select(Counter.value).where(Counter.name == "sa_seq")) or 0)


def _now() -> datetime:
    return datetime.now(UTC)


# ------------------------------------------------------------------ acceso
def get_assignment(db: Session, teacher: User, assignment_id: uuid.UUID) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if a is None:
        raise NotFoundError("Tarea no encontrada")
    get_teacher_classroom(db, teacher.id, a.classroom_id)  # ownership vía aula (404 si no es suya)
    return a


def get_variant(db: Session, teacher: User, assignment_id: uuid.UUID, variant_id: uuid.UUID
                ) -> tuple[Assignment, AssignmentVariant]:
    a = get_assignment(db, teacher, assignment_id)
    v = db.get(AssignmentVariant, variant_id)
    if v is None or v.assignment_id != a.id:
        raise NotFoundError("Variante no encontrada")
    return a, v


# ------------------------------------------------------------------ creación (respeta planificación vigente)
def create_assignment(db: Session, teacher: User, classroom_id: uuid.UUID, title: str, instructions: str, mode: str,
                      grade_topics: list[tuple[int, uuid.UUID]]) -> tuple[Assignment, list[AssignmentVariant]]:
    room = get_teacher_classroom(db, teacher.id, classroom_id)
    active = {v.id for v in active_versions_for_school_year(db, room.school_id, room.academic_year)}
    if not active:
        raise ConflictError("El aula no tiene una planificación vigente (versión ACTIVE) para su año escolar")
    resolved: list[tuple[int, CurriculumTopic, CurriculumUnit]] = []
    for grade_id, topic_id in grade_topics:
        topic = db.get(CurriculumTopic, topic_id)
        unit = db.get(CurriculumUnit, topic.unit_id) if topic else None
        if topic is None or unit is None or unit.version_id not in active:
            raise ConflictError("El tema no pertenece a la planificación vigente de la institución")
        if unit.grade_id != grade_id:
            raise ConflictError("El tema no corresponde al grado seleccionado según la planificación")
        resolved.append((grade_id, topic, unit))
    if len({u.subject_id for _, _, u in resolved}) != 1:
        raise ConflictError("Una tarea debe pertenecer a una sola área")
    if len({u.version_id for _, _, u in resolved}) != 1:
        raise ConflictError("Los temas deben provenir de la misma versión de planificación")
    a = Assignment(school_id=room.school_id, classroom_id=room.id, teacher_id=teacher.id,
                   plan_version_id=resolved[0][2].version_id, subject_id=resolved[0][2].subject_id, mode=mode,
                   title=title.strip(), base_instructions=instructions.strip())
    db.add(a)
    db.flush()
    variants = []
    for grade_id, topic, unit in resolved:
        v = AssignmentVariant(assignment_id=a.id, grade_id=grade_id, topic_id=topic.id,
                              competency_id=topic.competency_id, period_id=unit.period_id,
                              learning_objective=topic.learning_objective, title=a.title,
                              instructions=a.base_instructions)
        db.add(v)
        variants.append(v)
    db.commit()
    return a, variants


def create_ai_generated_variant_content(db: Session, variant: AssignmentVariant, title: str, instructions: str,
                                        generated_by: str) -> None:
    """Punto de entrada para el AI Gateway (Fase 11-12): el contenido SIEMPRE entra como AI_GENERATED."""
    if variant.status == "PUBLISHED":
        raise ConflictError("La variante ya está publicada")
    variant.title, variant.instructions = title, instructions
    variant.source, variant.generated_by, variant.status = "AI", generated_by, "AI_GENERATED"
    variant.approved_by = variant.approved_at = None
    db.commit()


# ------------------------------------------------------------------ edición
def _reset_translations(db: Session, variant_id: uuid.UUID) -> None:
    db.execute(update(VariantTranslation).where(VariantTranslation.variant_id == variant_id)
               .values(status="DRAFT", verified_by=None, verified_at=None))


def apply_ai_content(db: Session, variant: AssignmentVariant, content, generated_by: str, status: str,
                     notes: list[str]) -> None:
    """Contenido de IA: entra SIEMPRE como AI_GENERATED, sin aprobación. El docente debe revisarlo."""
    if variant.status == "PUBLISHED":
        raise ConflictError("La variante ya está publicada")
    variant.title, variant.instructions = content.title, content.instructions
    variant.source, variant.generated_by, variant.status = "AI", generated_by, "AI_GENERATED"
    variant.approved_by = variant.approved_at = None
    variant.validation_status = "OK" if status == "GENERATED" else "NEEDS_REVIEW"
    variant.validation_notes = notes or None
    db.execute(delete(Question).where(Question.variant_id == variant.id))
    db.add_all([Question(variant_id=variant.id, position=i + 1, **q.model_dump()) for i, q in enumerate(content.questions)])
    _reset_translations(db, variant.id)
    db.flush()

def _invalidate_approval(v: AssignmentVariant) -> None:
    """Cualquier cambio de contenido anula la aprobación previa y devuelve a revisión/borrador."""
    v.approved_by = v.approved_at = None
    if v.source in ("AI", "AI_EDITED"):
        v.source, v.status = "AI_EDITED", "TEACHER_REVIEW"
    else:
        v.status = "DRAFT"


def update_variant(db: Session, teacher: User, assignment_id: uuid.UUID, variant_id: uuid.UUID,
                   title: str | None, instructions: str | None) -> AssignmentVariant:
    _, v = get_variant(db, teacher, assignment_id, variant_id)
    if v.status == "PUBLISHED":
        raise ConflictError("La variante publicada no se modifica")
    if title is not None:
        v.title = title.strip()
    if instructions is not None:
        v.instructions = instructions.strip()
    _invalidate_approval(v)
    _reset_translations(db, v.id)
    db.commit()
    return v


def replace_questions(db: Session, teacher: User, assignment_id: uuid.UUID, variant_id: uuid.UUID,
                      questions: list[dict[str, Any]]) -> list[Question]:
    _, v = get_variant(db, teacher, assignment_id, variant_id)
    if v.status == "PUBLISHED":
        raise ConflictError("La variante publicada no se modifica")
    db.execute(delete(Question).where(Question.variant_id == v.id))
    rows = [Question(variant_id=v.id, position=i + 1, **q) for i, q in enumerate(questions)]
    db.add_all(rows)
    _invalidate_approval(v)
    _reset_translations(db, v.id)
    db.commit()
    return rows


# ------------------------------------------------------------------ revisión / aprobación (humano en el bucle)
def open_review(db: Session, teacher: User, assignment_id: uuid.UUID, variant_id: uuid.UUID) -> AssignmentVariant:
    _, v = get_variant(db, teacher, assignment_id, variant_id)
    if v.status not in ("DRAFT", "AI_GENERATED"):
        raise ConflictError(f"No se puede abrir revisión desde {v.status}")
    v.status = "TEACHER_REVIEW"
    db.commit()
    return v


def approve_variant(db: Session, teacher: User, assignment_id: uuid.UUID, variant_id: uuid.UUID,
                    acknowledge_warnings: bool = False) -> AssignmentVariant:
    _, v = get_variant(db, teacher, assignment_id, variant_id)
    if v.validation_status == "NEEDS_REVIEW" and v.status == "TEACHER_REVIEW" and not acknowledge_warnings:
        raise ConflictError("El validador curricular marcó advertencias; revísalas y confirma con acknowledge_warnings=true")
    if v.status == "AI_GENERATED":
        raise ConflictError("El contenido generado por IA debe pasar primero por revisión docente")
    if v.status == "DRAFT" and v.source != "TEACHER":
        raise ConflictError("Contenido de origen IA requiere revisión docente")
    if v.status not in ("DRAFT", "TEACHER_REVIEW"):
        raise ConflictError(f"No se puede aprobar desde {v.status}")
    if db.scalar(select(Question.id).where(Question.variant_id == v.id).limit(1)) is None:
        raise ConflictError("La variante no tiene preguntas")
    v.status, v.approved_by, v.approved_at = "APPROVED", teacher.id, _now()
    db.commit()
    return v


# ------------------------------------------------------------------ publicación
def _assign(db: Session, a: Assignment, variants_by_grade: dict[int, AssignmentVariant], room: Classroom,
            only_student: uuid.UUID | None = None) -> tuple[int, list[uuid.UUID]]:
    q = (select(StudentProfile.user_id, StudentProfile.grade_id)
         .join(ClassroomStudent, ClassroomStudent.student_user_id == StudentProfile.user_id)
         .where(ClassroomStudent.classroom_id == room.id, ClassroomStudent.left_at.is_(None)))
    if only_student:
        q = q.where(StudentProfile.user_id == only_student)
    assigned, without = 0, []
    for user_id, grade_id in db.execute(q):
        variant = variants_by_grade.get(grade_id)
        if variant is None:
            without.append(user_id)  # sin variante para su grado: NO se le asigna otra
            continue
        exists = db.scalar(select(StudentAssignment.id).where(StudentAssignment.assignment_id == a.id,
                                                              StudentAssignment.student_user_id == user_id))
        if exists is None:
            db.add(StudentAssignment(assignment_id=a.id, variant_id=variant.id, student_user_id=user_id, seq=next_seq(db)))
            assigned += 1
    return assigned, without


def publish(db: Session, teacher: User, assignment_id: uuid.UUID) -> dict:
    a = get_assignment(db, teacher, assignment_id)
    if a.status != "DRAFT":
        raise ConflictError(f"La tarea está en estado {a.status}")
    variants = list(db.scalars(select(AssignmentVariant).where(AssignmentVariant.assignment_id == a.id)))
    pending = [v.grade_id for v in variants if v.status != "APPROVED"]
    if not variants or pending:
        raise ConflictError(f"Todas las variantes deben estar aprobadas por el docente (pendientes: grados {pending})")
    now = _now()
    for v in variants:
        v.status, v.published_at = "PUBLISHED", now
    a.status, a.published_at = "PUBLISHED", now
    room = db.get(Classroom, a.classroom_id)
    assert room is not None
    assigned, without = _assign(db, a, {v.grade_id: v for v in variants}, room)
    events.emit(db, events.ASSIGNMENT_PUBLISHED, {"assignment_id": str(a.id), "classroom_id": str(a.classroom_id),
                                                  "teacher_id": str(teacher.id), "students_assigned": assigned})
    db.commit()
    return {"id": a.id, "status": a.status, "students_assigned": assigned,
            "students_without_variant": [str(s) for s in without]}


def assign_published_to_new_student(db: Session, room: Classroom, student_id: uuid.UUID) -> None:
    """Alumno que se une después: recibe las tareas ya publicadas del aula (variante de SU grado)."""
    for a in db.scalars(select(Assignment).where(Assignment.classroom_id == room.id, Assignment.status == "PUBLISHED")):
        vs = {v.grade_id: v for v in db.scalars(select(AssignmentVariant).where(AssignmentVariant.assignment_id == a.id))}
        _assign(db, a, vs, room, only_student=student_id)


# ------------------------------------------------------------------ lectura
def question_out(q: Question, *, include_answer: bool) -> dict:
    out = {"id": q.id, "position": q.position, "type": q.type, "prompt": q.prompt, "options": q.options,
           "difficulty": q.difficulty}
    if include_answer:
        out |= {"correct_answer": q.correct_answer, "hints": q.hints, "explanation": q.explanation}
    return out


def assignment_detail(db: Session, a: Assignment) -> dict:
    variants = []
    for v in db.scalars(select(AssignmentVariant).where(AssignmentVariant.assignment_id == a.id)
                        .order_by(AssignmentVariant.grade_id)):
        qs = db.scalars(select(Question).where(Question.variant_id == v.id).order_by(Question.position))
        variants.append({"id": v.id, "grade_id": v.grade_id, "topic_id": v.topic_id, "competency_id": v.competency_id,
                         "period_id": v.period_id, "learning_objective": v.learning_objective, "title": v.title,
                         "instructions": v.instructions, "status": v.status, "source": v.source,
                         "generated_by": v.generated_by, "approved_by": v.approved_by,
                         "validation_status": v.validation_status, "validation_notes": v.validation_notes,
                         "questions": [question_out(q, include_answer=True) for q in qs]})
    return {"id": a.id, "classroom_id": a.classroom_id, "plan_version_id": a.plan_version_id,
            "subject_id": a.subject_id, "mode": a.mode, "title": a.title, "status": a.status, "variants": variants}


def student_tasks(db: Session, student: User) -> list[dict]:
    rows = db.execute(
        select(StudentAssignment, AssignmentVariant, Assignment)
        .join(AssignmentVariant, AssignmentVariant.id == StudentAssignment.variant_id)
        .join(Assignment, Assignment.id == StudentAssignment.assignment_id)
        .where(StudentAssignment.student_user_id == student.id, AssignmentVariant.status == "PUBLISHED",
               StudentAssignment.origin == "TEACHER")
        .order_by(StudentAssignment.created_at))
    out = []
    for sa, v, a in rows:
        qs = db.scalars(select(Question).where(Question.variant_id == v.id).order_by(Question.position))
        out.append({"student_assignment_id": sa.id, "assignment_id": a.id, "variant_id": v.id, "grade_id": v.grade_id,
                    "title": v.title, "instructions": v.instructions, "learning_objective": v.learning_objective,
                    "status": sa.status, "questions": [question_out(q, include_answer=False) for q in qs]})
    return out
