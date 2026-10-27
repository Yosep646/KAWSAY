import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain import adaptive
from app.modules.assignments.models import AssignmentVariant, Question
from app.modules.automation import events
from app.modules.classrooms.models import ClassroomStudent, ClassroomTeacher
from app.modules.learning.models import LearningAttempt, StudentCompetencyProgress
from app.modules.planning.models import CurriculumTopic
from app.modules.support_flags.models import SupportFlag


def recompute_and_detect(db: Session, student_id: uuid.UUID, competency_id: uuid.UUID) -> None:
    """Intento -> progreso por competencia -> PatternDetector -> SupportFlag (todo en backend, sin n8n/IA)."""
    rows = db.scalars(select(LearningAttempt).where(LearningAttempt.student_user_id == student_id,
                                                     LearningAttempt.competency_id == competency_id))
    facts = [adaptive.AttemptFact(str(a.id), str(a.question_id), a.attempt_number, a.is_correct, a.hints_used,
                                  a.effective_at) for a in rows]
    results = adaptive.question_results(facts)
    score, evidence_count = adaptive.compute_progress(results)
    state = adaptive.level_for(score)

    prog = db.scalar(select(StudentCompetencyProgress).where(StudentCompetencyProgress.student_user_id == student_id,
                                                              StudentCompetencyProgress.competency_id == competency_id))
    if prog is None:
        prog = StudentCompetencyProgress(student_user_id=student_id, competency_id=competency_id,
                                         evidence_count=evidence_count, method_version=adaptive.METHOD_VERSION)
        db.add(prog)
    prog.score, prog.evidence_count, prog.state = score, evidence_count, state
    prog.method_version, prog.computed_at = adaptive.METHOD_VERSION, datetime.now(UTC)

    finding = adaptive.detect_difficulty(results)
    if finding is not None:
        flag = _upsert_flag(db, student_id, competency_id, finding)
        if flag is not None:
            rooms = list(db.execute(select(ClassroomStudent.classroom_id, ClassroomTeacher.teacher_user_id).join(
                ClassroomTeacher, ClassroomTeacher.classroom_id == ClassroomStudent.classroom_id).where(
                ClassroomStudent.student_user_id == student_id, ClassroomStudent.left_at.is_(None))))
            events.emit(db, events.SUPPORT_FLAG_CREATED, {
                "flag_id": str(flag.id), "rule_id": flag.rule_id, "competency_id": str(competency_id),
                "classroom_ids": sorted({str(r) for r, _ in rooms}), "teacher_ids": sorted({str(t) for _, t in rooms})})
    db.flush()


def _topic_titles(db: Session, question_ids: list[str]) -> dict[str, str]:
    q = (select(Question.id, CurriculumTopic.title)
         .join(AssignmentVariant, AssignmentVariant.id == Question.variant_id)
         .join(CurriculumTopic, CurriculumTopic.id == AssignmentVariant.topic_id)
         .where(Question.id.in_([uuid.UUID(x) for x in question_ids])))
    return {str(qid): title for qid, title in db.execute(q)}


def _upsert_flag(db: Session, student_id: uuid.UUID, competency_id: uuid.UUID,
                 f: adaptive.DifficultyFinding) -> SupportFlag | None:
    titles = _topic_titles(db, [r["question_id"] for r in f.results])
    evidence = {"window": f.window, "difficult": f.difficult, "hints_total": f.hints_total,
                "wrong_attempts_total": f.wrong_attempts_total, "distinct_days": f.distinct_days,
                "topics": sorted(set(titles.values())),
                "results": [{**r, "topic": titles.get(r["question_id"])} for r in f.results]}
    existing = db.scalar(select(SupportFlag).where(
        SupportFlag.student_user_id == student_id, SupportFlag.competency_id == competency_id,
        SupportFlag.rule_id == f.rule_id, SupportFlag.status.in_(("OPEN", "ACKNOWLEDGED"))))
    if existing is not None:
        existing.evidence = evidence  # se actualiza la evidencia; no se duplica el flag
        return None
    flag = SupportFlag(student_user_id=student_id, competency_id=competency_id, rule_id=f.rule_id,
                       rule_version=f.rule_version, evidence=evidence, recommendation_code="GUIDED_ACTIVITY")
    try:
        with db.begin_nested():
            db.add(flag)
    except IntegrityError:
        return None  # carrera: otro proceso lo creó
    return flag
