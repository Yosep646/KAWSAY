import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppError, ConflictError
from app.core.permissions import require_roles
from app.core.rate_limit import check_rate
from app.modules.ai.adaptation import PROMPT_VERSION, adapt_one
from app.modules.ai.gateway import AIGateway, get_gateway
from app.modules.assignments import service
from app.modules.assignments.math_grade_rules import RULE_VERSION, generate_questions, instructions_for_grade, parse_example
from app.modules.assignments.models import Assignment, AssignmentVariant
from app.modules.assignments.schemas import QuestionsIn
from app.modules.classrooms.service import list_teacher_classrooms
from app.modules.curriculum.models import Grade, Subject
from app.modules.planning.models import CurriculumTopic
from app.modules.users.models import Role, User

router = APIRouter(prefix="/assignments", tags=["assignments"])
DB = Annotated[Session, Depends(get_db)]
Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]
Student = Annotated[User, Depends(require_roles(Role.STUDENT))]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GradeTopic(_In):
    grade_id: int = Field(ge=1)
    topic_id: uuid.UUID


class AssignmentIn(_In):
    classroom_id: uuid.UUID
    title: str = Field(min_length=2, max_length=300)
    instructions: str = Field(min_length=5, max_length=5000)
    mode: Literal["MANUAL", "AI_ASSISTED", "ADAPTIVE_POOL"] = "MANUAL"
    grade_topics: list[GradeTopic] = Field(min_length=1, max_length=11)

    @field_validator("mode")
    @classmethod
    def _implemented(cls, v: str) -> str:
        if v == "ADAPTIVE_POOL":
            raise ValueError("ADAPTIVE_POOL aún no está implementado")  # PLANNED, no se simula
        return v

    @model_validator(mode="after")
    def _unique_grades(self) -> "AssignmentIn":
        if len({g.grade_id for g in self.grade_topics}) != len(self.grade_topics):
            raise ValueError("Grados repetidos")
        return self


class VariantPatch(_In):
    title: str | None = Field(default=None, min_length=2, max_length=300)
    instructions: str | None = Field(default=None, min_length=5, max_length=5000)


class NotImplementedYet(AppError):
    status_code = 501
    code = "not_implemented"


@router.post("", status_code=201)
def create(body: AssignmentIn, db: DB, teacher: Teacher) -> dict:
    a, _ = service.create_assignment(db, teacher, body.classroom_id, body.title, body.instructions, body.mode,
                                     [(g.grade_id, g.topic_id) for g in body.grade_topics])
    return service.assignment_detail(db, a)


@router.get("")
def list_mine(db: DB, teacher: Teacher) -> list[dict]:
    rooms = [r.id for r in list_teacher_classrooms(db, teacher.id)]
    rows = db.scalars(select(Assignment).where(Assignment.classroom_id.in_(rooms)).order_by(Assignment.created_at.desc()))
    return [{"id": a.id, "classroom_id": a.classroom_id, "title": a.title, "status": a.status, "mode": a.mode}
            for a in rows]


@router.get("/mine")
def my_tasks(db: DB, student: Student) -> list[dict]:
    """Tareas publicadas del estudiante: SOLO la variante de su grado, sin respuestas ni pistas."""
    return service.student_tasks(db, student)


@router.get("/{assignment_id}")
def detail(assignment_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    return service.assignment_detail(db, service.get_assignment(db, teacher, assignment_id))


@router.patch("/{assignment_id}/variants/{variant_id}")
def patch_variant(assignment_id: uuid.UUID, variant_id: uuid.UUID, body: VariantPatch, db: DB, teacher: Teacher) -> dict:
    v = service.update_variant(db, teacher, assignment_id, variant_id, body.title, body.instructions)
    return {"id": v.id, "status": v.status, "source": v.source}


@router.put("/{assignment_id}/variants/{variant_id}/questions")
def put_questions(assignment_id: uuid.UUID, variant_id: uuid.UUID, body: QuestionsIn, db: DB, teacher: Teacher) -> dict:
    rows = service.replace_questions(db, teacher, assignment_id, variant_id, [q.model_dump() for q in body.questions])
    return {"count": len(rows)}


@router.post("/{assignment_id}/variants/{variant_id}/review")
def review(assignment_id: uuid.UUID, variant_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    v = service.open_review(db, teacher, assignment_id, variant_id)
    return {"id": v.id, "status": v.status}


@router.post("/{assignment_id}/variants/{variant_id}/approve")
def approve(assignment_id: uuid.UUID, variant_id: uuid.UUID, db: DB, teacher: Teacher,
            acknowledge_warnings: bool = False) -> dict:
    v = service.approve_variant(db, teacher, assignment_id, variant_id, acknowledge_warnings)
    return {"id": v.id, "status": v.status, "approved_by": v.approved_by}


@router.post("/{assignment_id}/publish")
def publish(assignment_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    return service.publish(db, teacher, assignment_id)


class MathGradeAdaptIn(_In):
    source_grade_id: int = Field(ge=1)
    example: str = Field(min_length=3, max_length=36)

    @field_validator("example")
    @classmethod
    def _is_arithmetic(cls, value: str) -> str:
        parse_example(value)
        return value


@router.post("/{assignment_id}/adapt-math")
def adapt_math_by_rules(assignment_id: uuid.UUID, body: MathGradeAdaptIn,
                        db: DB, teacher: Teacher) -> dict:
    """Offline-capable arithmetic differentiation. No provider keys or ML involved.

    The six grade variants must already belong to the school's ACTIVE plan
    (same mathematics competency and area). Never publishes or approves.
    """
    assignment = service.get_assignment(db, teacher, assignment_id)
    if assignment.status != "DRAFT":
        raise ConflictError("Solo se adaptan actividades todavía no publicadas")
    subject = db.get(Subject, assignment.subject_id)
    if not subject or "matem" not in subject.name.casefold():
        raise ConflictError("La automatización por reglas solo admite el área de Matemática")
    variants = list(db.scalars(select(AssignmentVariant).where(
        AssignmentVariant.assignment_id == assignment.id).order_by(AssignmentVariant.grade_id)))
    source = next((v for v in variants if v.grade_id == body.source_grade_id), None)
    if source is None:
        raise ConflictError("El grado de origen debe tener una variante en la planificación activa")
    source_grade = db.get(Grade, source.grade_id)
    if source_grade is None or source_grade.level != "PRIMARIA":
        raise ConflictError("Solo se admiten grados de primaria")
    example = parse_example(body.example)
    prepared = []
    # Validate ALL variants BEFORE writing ANY: no partial generation or mixed competencies.
    for variant in variants:
        grade = db.get(Grade, variant.grade_id)
        topic = db.get(CurriculumTopic, variant.topic_id)
        if grade is None or grade.level != "PRIMARIA" or not 1 <= grade.number <= 6:
            raise ConflictError("Las variantes deben corresponder a grados de primaria")
        if topic is None or variant.competency_id != source.competency_id:
            raise ConflictError("Cada grado requiere un tema revisado de la misma competencia en la malla vigente")
        questions = generate_questions(example, grade.number, source_grade.number)
        prepared.append((variant, grade, topic, questions))
    for variant, grade, topic, questions in prepared:
        title = f"{assignment.title} · {grade.number}.º primaria"
        instructions = instructions_for_grade(grade.number, source_grade.number,
                                               topic.title, variant.learning_objective)
        service.apply_math_rule_content(
            db, variant, title, instructions,
            [q.model_dump() for q in questions], f"RULES/{RULE_VERSION}",
        )
    db.commit()
    return {
        "assignment_id": assignment.id, "engine": "RULES", "rule_version": RULE_VERSION,
        "source_grade_id": source_grade.id, "status": "TEACHER_REVIEW",
        "variants": [{"variant_id":v.id, "grade_id":g.id, "grade_number":g.number,
                      "questions":len(questions), "status":v.status}
                     for v,g,_,questions in prepared],
        "note": "Los ejercicios generados requieren revisión y aprobación docente antes de publicar.",
    }


class AdaptIn(_In):
    grade_ids: list[int] | None = Field(default=None, max_length=11)
    constraints: str | None = Field(default=None, max_length=1000)


class AIUnavailableError(AppError):
    status_code = 503
    code = "ai_unavailable"


@router.post("/{assignment_id}/adapt")
def adapt(assignment_id: uuid.UUID, body: AdaptIn, db: DB, teacher: Teacher,
          gateway: Annotated[AIGateway, Depends(get_gateway)]) -> dict:
    """KAWSAY propone variantes por grado. Todo entra como AI_GENERATED: el docente revisa, edita y aprueba."""
    check_rate(f"ai:{teacher.id}", 10, 60)
    a = service.get_assignment(db, teacher, assignment_id)
    if a.mode != "AI_ASSISTED":
        raise ConflictError("La adaptación con IA requiere una tarea en modo AI_ASSISTED")
    if a.status != "DRAFT":
        raise ConflictError("La tarea ya fue publicada")
    variants = list(db.scalars(select(AssignmentVariant).where(AssignmentVariant.assignment_id == a.id)
                               .order_by(AssignmentVariant.grade_id)))
    if body.grade_ids is not None:
        variants = [v for v in variants if v.grade_id in body.grade_ids]
    results = []
    for v in variants:
        r = adapt_one(db, gateway, teacher.id, a, v, body.constraints)
        if r.content is not None:
            service.apply_ai_content(db, v, r.content, f"{r.provider}/{r.model}@{PROMPT_VERSION}", r.status, r.reasons)
        results.append({"variant_id": v.id, "grade_id": v.grade_id, "status": r.status, "reasons": r.reasons})
    db.commit()
    if results and all(x["status"] in ("UNAVAILABLE", "TIMEOUT") for x in results):
        raise AIUnavailableError("La IA no está disponible ahora. Puedes crear las variantes manualmente; "
                                 "el resto de KAWSAY sigue funcionando.")
    return {"assignment_id": a.id, "results": results}
