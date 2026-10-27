import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import get_current_user, require_roles
from app.modules.assignments import service as assignments
from app.modules.assignments.models import AssignmentVariant, Question, StudentAssignment
from app.modules.audit.service import log_access
from app.modules.classrooms.service import teacher_can_access_student
from app.modules.languages.models import Language, LanguageVariant, StudentLanguage, VariantTranslation
from app.modules.users.models import Role, User

router = APIRouter(tags=["languages"])
DB = Annotated[Session, Depends(get_db)]
Teacher = Annotated[User, Depends(require_roles(Role.TEACHER))]
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]
Student = Annotated[User, Depends(require_roles(Role.STUDENT))]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VariantIn(_In):
    language_code: str = Field(min_length=2, max_length=8)
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    note: str | None = Field(default=None, max_length=1000)


class LanguagesIn(_In):
    mother_language_code: str | None = Field(default=None, max_length=8)
    mother_variant_id: uuid.UUID | None = None
    preferred_language_code: str | None = Field(default=None, max_length=8)


class LanguagesOut(BaseModel):
    mother_language: str | None
    mother_variant_id: uuid.UUID | None
    preferred_language: str | None


class TranslationIn(_In):
    language_code: str = Field(min_length=2, max_length=8)
    language_variant_id: uuid.UUID | None = None
    title: str = Field(min_length=2, max_length=300)
    instructions: str = Field(min_length=5, max_length=5000)
    question_prompts: dict[uuid.UUID, Annotated[str, Field(min_length=1, max_length=2000)]] = Field(default_factory=dict)


def _lang(db: Session, code: str) -> Language:
    lang = db.scalar(select(Language).where(Language.code == code.lower()))
    if lang is None:
        raise NotFoundError(f"Idioma no soportado: {code}")
    return lang


@router.get("/languages")
def list_languages(db: DB, _: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    out = []
    for lang in db.scalars(select(Language).order_by(Language.code)):
        vs = db.scalars(select(LanguageVariant).where(LanguageVariant.language_id == lang.id).order_by(LanguageVariant.name))
        out.append({"code": lang.code, "name": lang.name,
                    "variants": [{"id": v.id, "code": v.code, "name": v.name, "note": v.note} for v in vs]})
    return out


@router.post("/languages/variants", status_code=201)
def create_variant(body: VariantIn, db: DB, _: Admin) -> dict:
    v = LanguageVariant(language_id=_lang(db, body.language_code).id, code=body.code, name=body.name, note=body.note)
    db.add(v)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("La variante ya existe") from exc
    return {"id": v.id}


def _save_languages(db: Session, student_id: uuid.UUID, body: LanguagesIn) -> dict:
    """Solo se guarda lo que la persona declara. NUNCA se infiere el idioma por ubicación."""
    row = db.get(StudentLanguage, student_id) or StudentLanguage(student_user_id=student_id)
    mother = _lang(db, body.mother_language_code) if body.mother_language_code else None
    if body.mother_variant_id is not None:
        var = db.get(LanguageVariant, body.mother_variant_id)
        if mother is None or var is None or var.language_id != mother.id:
            raise ConflictError("La variante no corresponde a la lengua materna indicada")
    previous_preferred_id = row.preferred_language_id
    row.mother_language_id = mother.id if mother else None
    row.mother_variant_id = body.mother_variant_id
    row.preferred_language_id = _lang(db, body.preferred_language_code).id if body.preferred_language_code else None
    db.add(row)
    if row.preferred_language_id != previous_preferred_id:
        for student_assignment in db.scalars(
            select(StudentAssignment).where(StudentAssignment.student_user_id == student_id)
        ):
            student_assignment.seq = assignments.next_seq(db)
    db.commit()
    return _read_languages(db, student_id)


def _read_languages(db: Session, student_id: uuid.UUID) -> dict:
    row = db.get(StudentLanguage, student_id)
    code = lambda i: db.scalar(select(Language.code).where(Language.id == i)) if i else None  # noqa: E731
    return {"mother_language": code(row.mother_language_id) if row else None,
            "mother_variant_id": row.mother_variant_id if row else None,
            "preferred_language": code(row.preferred_language_id) if row else None}


@router.get("/students/me/languages", response_model=LanguagesOut)
def my_languages(db: DB, student: Student) -> dict:
    return _read_languages(db, student.id)


@router.put("/students/me/languages", response_model=LanguagesOut)
def set_my_languages(body: LanguagesIn, db: DB, student: Student) -> dict:
    return _save_languages(db, student.id, body)


@router.get("/students/{student_id}/languages", response_model=LanguagesOut)
def get_student_languages(student_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    if not teacher_can_access_student(db, teacher.id, student_id):
        raise NotFoundError("Estudiante no encontrado")
    result = _read_languages(db, student_id)
    log_access(db, teacher, "students.languages.read", "student", student_id)
    return result


@router.put("/students/{student_id}/languages", response_model=LanguagesOut)
def set_student_languages(student_id: uuid.UUID, body: LanguagesIn, db: DB, teacher: Teacher) -> dict:
    if not teacher_can_access_student(db, teacher.id, student_id):
        raise NotFoundError("Estudiante no encontrado")
    return _save_languages(db, student_id, body)


# ---------------------------------------------------------------- traducciones (humanas, verificadas)
@router.post("/assignments/{assignment_id}/variants/{variant_id}/translations", status_code=201)
def upsert_translation(assignment_id: uuid.UUID, variant_id: uuid.UUID, body: TranslationIn, db: DB, teacher: Teacher) -> dict:
    _, v = assignments.get_variant(db, teacher, assignment_id, variant_id)
    if v.status not in ("APPROVED", "PUBLISHED"):
        raise ConflictError("Solo se traducen variantes aprobadas o publicadas")
    lang = _lang(db, body.language_code)
    if lang.code == "es":
        raise ConflictError("El español es el idioma base")
    if body.language_variant_id is not None:
        lv = db.get(LanguageVariant, body.language_variant_id)
        if lv is None or lv.language_id != lang.id:
            raise ConflictError("La variante no corresponde al idioma")
    qids = set(db.scalars(select(Question.id).where(Question.variant_id == v.id)))
    if not set(body.question_prompts) <= qids:
        raise ConflictError("question_prompts contiene preguntas que no son de esta variante")
    tr = db.scalar(select(VariantTranslation).where(VariantTranslation.variant_id == v.id,
                                                    VariantTranslation.language_id == lang.id))
    if tr is None:
        tr = VariantTranslation(variant_id=v.id, language_id=lang.id, created_by=teacher.id, title=body.title,
                                instructions=body.instructions)
        db.add(tr)
    tr.language_variant_id, tr.title, tr.instructions = body.language_variant_id, body.title, body.instructions
    tr.question_prompts = {str(k): t for k, t in body.question_prompts.items()}
    tr.status, tr.verified_by, tr.verified_at = "DRAFT", None, None   # cualquier cambio exige nueva verificación
    db.commit()
    return {"id": tr.id, "status": tr.status}


def _translation(db: Session, tid: uuid.UUID) -> VariantTranslation:
    tr = db.get(VariantTranslation, tid)
    if tr is None:
        raise NotFoundError("Traducción no encontrada")
    return tr


@router.post("/translations/{translation_id}/submit")
def submit_translation(translation_id: uuid.UUID, db: DB, teacher: Teacher) -> dict:
    tr = _translation(db, translation_id)
    v = db.get(AssignmentVariant, tr.variant_id)
    assert v is not None
    assignments.get_assignment(db, teacher, v.assignment_id)  # ownership
    if tr.status != "DRAFT":
        raise ConflictError(f"Estado inválido: {tr.status}")
    tr.status = "IN_REVIEW"
    db.commit()
    return {"id": tr.id, "status": tr.status}


@router.post("/translations/{translation_id}/verify")
def verify_translation(translation_id: uuid.UUID, db: DB, reviewer: Admin) -> dict:
    tr = _translation(db, translation_id)
    if tr.status != "IN_REVIEW":
        raise ConflictError(f"Estado inválido: {tr.status}")
    tr.status, tr.verified_by, tr.verified_at = "VERIFIED", reviewer.id, datetime.now(UTC)
    db.commit()
    return {"id": tr.id, "status": tr.status}


@router.post("/translations/{translation_id}/reject")
def reject_translation(translation_id: uuid.UUID, db: DB, _: Admin) -> dict:
    tr = _translation(db, translation_id)
    if tr.status != "IN_REVIEW":
        raise ConflictError(f"Estado inválido: {tr.status}")
    tr.status = "REJECTED"
    db.commit()
    return {"id": tr.id, "status": tr.status}
