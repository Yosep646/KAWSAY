import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.adaptive import evaluate_answer
from app.modules.assignments import service as assignments
from app.modules.assignments.models import Assignment, AssignmentVariant, Question, StudentAssignment
from app.modules.automation import events as domain_events
from app.modules.curriculum.models import Competency, Subject
from app.modules.languages.models import Language, StudentLanguage, VariantTranslation
from app.modules.learning.models import LearningAttempt
from app.modules.learning.service import recompute_and_detect
from app.modules.planning.models import CurriculumTopic
from app.modules.sync.models import SyncEvent
from app.modules.users.models import User

MAX_BATCH = 100


class AttemptPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_assignment_id: uuid.UUID
    question_id: uuid.UUID
    attempt_number: int = Field(ge=1, le=50)
    answer: dict[str, Any]
    is_correct: bool | None = None
    hints_used: int = Field(ge=0, le=20)
    response_time_ms: int = Field(ge=0, le=3_600_000)
    client_created_at: datetime


def _result(event_id: uuid.UUID, status: str, reason: str | None = None) -> dict:
    out = {"event_id": str(event_id), "status": status}
    if reason:
        out["reason"] = reason
    return out


def _record(db: Session, student: User, device_id: uuid.UUID, event_id: uuid.UUID, etype: str, status: str,
            reason: str | None) -> None:
    db.add(SyncEvent(event_id=event_id, device_id=device_id, student_user_id=student.id, type=etype[:40],
                     status=status, reason=reason))


def _apply_attempt(db: Session, student: User, device_id: uuid.UUID, event_id: uuid.UUID, p: AttemptPayload
                   ) -> tuple[str | None, uuid.UUID | None]:
    """Devuelve (motivo_de_rechazo, competency_id). Todo se revalida en servidor."""
    sa = db.get(StudentAssignment, p.student_assignment_id)
    if sa is None or sa.student_user_id != student.id:
        return "student_assignment_not_found", None
    q = db.get(Question, p.question_id)
    variant = db.get(AssignmentVariant, sa.variant_id)
    if q is None or variant is None or q.variant_id != variant.id or variant.status != "PUBLISHED":
        return "question_not_in_assignment", None
    correct = evaluate_answer(q.type, q.correct_answer, p.answer)
    if correct is None:
        return "invalid_answer", None
    now = datetime.now(UTC)
    created = p.client_created_at if p.client_created_at.tzinfo else p.client_created_at.replace(tzinfo=UTC)
    db.add(LearningAttempt(
        id=event_id, student_user_id=student.id, student_assignment_id=sa.id, question_id=q.id,
        competency_id=variant.competency_id, device_id=device_id, attempt_number=p.attempt_number, answer=p.answer,
        is_correct=correct, client_is_correct=p.is_correct, hints_used=p.hints_used,
        response_time_ms=p.response_time_ms, client_created_at=created,
        effective_at=min(created, now), received_at=now))  # un reloj adelantado no puede inflar el orden temporal
    if sa.status == "ASSIGNED":
        sa.status = "IN_PROGRESS"
    return None, variant.competency_id


def _same_attempt(db: Session, event_id: uuid.UUID, raw: dict) -> bool:
    """Solo confirmar un reenvío si coincide con el intento persistido."""
    if raw.get("type") != "attempt.created":
        return False
    try:
        p = AttemptPayload.model_validate(raw.get("payload") or {})
    except ValidationError:
        return False
    attempt = db.get(LearningAttempt, event_id)
    if attempt is None:
        return False
    created = p.client_created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return (attempt.student_assignment_id == p.student_assignment_id and attempt.question_id == p.question_id
            and attempt.attempt_number == p.attempt_number and attempt.answer == p.answer
            and attempt.client_is_correct == p.is_correct and attempt.hints_used == p.hints_used
            and attempt.response_time_ms == p.response_time_ms and attempt.client_created_at == created)


def push(db: Session, student: User, device_id: uuid.UUID, events: list[dict]) -> list[dict]:
    results: list[dict] = []
    affected: set[uuid.UUID] = set()
    for raw in events:
        try:
            event_id = uuid.UUID(str(raw.get("event_id")))
        except ValueError:
            results.append({"event_id": str(raw.get("event_id")), "status": "REJECTED", "reason": "invalid_event_id"})
            continue
        etype = str(raw.get("type", ""))
        existing = db.scalar(select(SyncEvent).where(SyncEvent.event_id == event_id))
        if existing is not None:
            if existing.student_user_id != student.id:
                results.append(_result(event_id, "REJECTED", "event_id_conflict"))
            elif existing.status == "ACKED":
                results.append(_result(event_id, "DUPLICATE") if _same_attempt(db, event_id, raw)
                               else _result(event_id, "REJECTED", "event_id_conflict"))
            else:
                results.append(_result(event_id, "REJECTED", existing.reason))
            continue
        reason: str | None = None
        competency: uuid.UUID | None = None
        try:
            with db.begin_nested():
                if etype != "attempt.created":
                    reason = "unsupported_event_type"
                else:
                    try:
                        payload = AttemptPayload.model_validate(raw.get("payload") or {})
                    except ValidationError:
                        reason = "invalid_payload"
                    else:
                        reason, competency = _apply_attempt(db, student, device_id, event_id, payload)
                if reason is None:
                    _record(db, student, device_id, event_id, etype, "ACKED", None)
                    db.flush()
                else:
                    raise _Rejected
        except _Rejected:
            pass
        except IntegrityError:
            reason = "duplicate_or_conflict"
            competency = None
        if reason is not None:
            existing = db.scalar(select(SyncEvent).where(SyncEvent.event_id == event_id))
            if reason == "duplicate_or_conflict" and existing is not None:
                if existing.student_user_id == student.id and existing.status == "ACKED" and _same_attempt(db, event_id, raw):
                    results.append(_result(event_id, "DUPLICATE"))
                else:
                    results.append(_result(event_id, "REJECTED", "event_id_conflict"))
                continue
            try:
                with db.begin_nested():
                    _record(db, student, device_id, event_id, etype, "REJECTED", reason)
            except IntegrityError:
                pass
            results.append(_result(event_id, "REJECTED", reason))
        else:
            results.append(_result(event_id, "ACKED"))
            if competency is not None:
                affected.add(competency)
    for comp in affected:
        recompute_and_detect(db, student.id, comp)
    counts = {k: sum(1 for r in results if r["status"] == k) for k in ("ACKED", "DUPLICATE", "REJECTED")}
    domain_events.emit(db, domain_events.SYNC_COMPLETED, {"student_id": str(student.id), **{k.lower(): v for k, v in counts.items()}})
    db.commit()
    return results


class _Rejected(Exception):  # noqa: N818 - control de flujo interno para revertir el savepoint
    pass


def preferred_language(db: Session, student: User) -> str | None:
    return db.scalar(select(Language.code).join(StudentLanguage, StudentLanguage.preferred_language_id == Language.id)
                     .where(StudentLanguage.student_user_id == student.id))


def task_payload(db: Session, sa: StudentAssignment, v: AssignmentVariant, pref: str | None) -> dict:
    """Tarea lista para trabajar OFFLINE (con respuestas y pistas: el cliente corrige localmente; el servidor re-corrige)."""
    qs = db.scalars(select(Question).where(Question.variant_id == v.id).order_by(Question.position))
    translation = None
    if pref and pref != "es":   # solo traducciones VERIFICADAS por una persona; nunca se inventan
        tr = db.scalar(select(VariantTranslation).join(Language, Language.id == VariantTranslation.language_id).where(
            VariantTranslation.variant_id == v.id, Language.code == pref, VariantTranslation.status == "VERIFIED"))
        if tr is not None:
            translation = {"language": pref, "title": tr.title, "instructions": tr.instructions,
                           "question_prompts": tr.question_prompts}
    a = db.get(Assignment, sa.assignment_id)
    subject = db.get(Subject, a.subject_id) if a else None
    comp = db.get(Competency, v.competency_id)
    topic = db.get(CurriculumTopic, v.topic_id)
    return {"subject": subject.name if subject else None, "competency_name": comp.name if comp else None,
            "topic_title": topic.title if topic else None,
            "language": {"preferred": pref, "translation_available": translation is not None},
            "translation": translation, "student_assignment_id": sa.id, "assignment_id": sa.assignment_id,
            "variant_id": v.id, "origin": sa.origin, "grade_id": v.grade_id, "title": v.title,
            "instructions": v.instructions, "learning_objective": v.learning_objective,
            "competency_id": v.competency_id, "topic_id": v.topic_id, "seq": sa.seq,
            "questions": [assignments.question_out(q, include_answer=True) for q in qs]}


def pull(db: Session, student: User, cursor: int, limit: int) -> dict:
    """Tareas nuevas (seq > cursor) con lo necesario para trabajar OFFLINE, más progreso oficial."""
    rows = list(db.execute(
        select(StudentAssignment).where(StudentAssignment.student_user_id == student.id,
                                        StudentAssignment.seq > cursor)
        .order_by(StudentAssignment.seq).limit(limit + 1)))
    has_more = len(rows) > limit
    rows = rows[:limit]
    pref = preferred_language(db, student)
    tasks = []
    for (sa,) in rows:
        v = db.get(AssignmentVariant, sa.variant_id)
        if v is not None and v.status == "PUBLISHED":
            tasks.append(task_payload(db, sa, v, pref))
    next_cursor = rows[-1][0].seq if rows else cursor
    from app.modules.learning.models import StudentCompetencyProgress
    prog = [{"competency_id": p.competency_id, "score": float(p.score) if p.score is not None else None,
             "evidence_count": p.evidence_count}
            for p in db.scalars(select(StudentCompetencyProgress).where(
                StudentCompetencyProgress.student_user_id == student.id))]
    return {"tasks": tasks, "progress": prog, "cursor": next_cursor, "has_more": has_more,
            "server_time": datetime.now(UTC).isoformat()}
