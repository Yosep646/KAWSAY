import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.classrooms.service import teacher_school_id
from app.modules.curriculum.models import Capacity, Competency, CurriculumFramework, Grade, Subject
from app.modules.planning.models import (
    AcademicPeriod,
    AcademicYear,
    CurriculumPlanVersion,
    CurriculumTopic,
    CurriculumUnit,
    SchoolCurriculumPlan,
)
from app.modules.users.models import Role, User


def _now() -> datetime:
    return datetime.now(UTC)


# ------------------------------------------------------------------ acceso (ownership por escuela)
def get_plan(db: Session, user: User, plan_id: uuid.UUID) -> SchoolCurriculumPlan:
    plan = db.get(SchoolCurriculumPlan, plan_id)
    if plan is None or (user.role == Role.TEACHER and plan.school_id != teacher_school_id(db, user.id)):
        raise NotFoundError("Planificación no encontrada")  # 404: no revelar existencia
    return plan


def get_version(db: Session, user: User, version_id: uuid.UUID) -> tuple[CurriculumPlanVersion, SchoolCurriculumPlan]:
    ver = db.get(CurriculumPlanVersion, version_id)
    if ver is None:
        raise NotFoundError("Versión no encontrada")
    return ver, get_plan(db, user, ver.plan_id)


def _require_draft(ver: CurriculumPlanVersion) -> None:
    if ver.status != "DRAFT":
        raise ConflictError(f"La versión {ver.label} está en estado {ver.status} y no es editable; "
                            "crea una nueva versión")


# ------------------------------------------------------------------ creación
def create_plan(
    db: Session, teacher: User, year: int, framework_id: uuid.UUID, name: str
) -> tuple[SchoolCurriculumPlan, CurriculumPlanVersion]:
    school_id = teacher_school_id(db, teacher.id)
    if db.get(CurriculumFramework, framework_id) is None:
        raise NotFoundError("Marco curricular no encontrado")
    ay = db.scalar(select(AcademicYear).where(AcademicYear.school_id == school_id, AcademicYear.year == year))
    if ay is None:
        ay = AcademicYear(school_id=school_id, year=year)
        db.add(ay)
        db.flush()
    plan = SchoolCurriculumPlan(school_id=school_id, academic_year_id=ay.id, framework_id=framework_id,
                                name=name.strip())
    db.add(plan)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Ya existe una planificación con ese nombre para ese año") from exc
    ver = CurriculumPlanVersion(plan_id=plan.id, label=f"{year}.1", created_by=teacher.id)
    db.add(ver)
    db.commit()
    return plan, ver


def add_period(db: Session, user: User, version_id: uuid.UUID, name: str, sequence: int,
               start: date | None, end: date | None) -> AcademicPeriod:
    ver, _ = get_version(db, user, version_id)
    _require_draft(ver)
    period = AcademicPeriod(version_id=ver.id, name=name.strip(), sequence=sequence, start_date=start, end_date=end)
    db.add(period)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Periodo duplicado o fechas inválidas") from exc
    return period


def add_unit(db: Session, user: User, version_id: uuid.UUID, period_id: uuid.UUID, grade_id: int,
             subject_id: uuid.UUID, title: str, sequence: int) -> CurriculumUnit:
    ver, plan = get_version(db, user, version_id)
    _require_draft(ver)
    period = db.get(AcademicPeriod, period_id)
    if period is None or period.version_id != ver.id:
        raise NotFoundError("Periodo no encontrado en esta versión")
    if db.get(Grade, grade_id) is None:
        raise NotFoundError("Grado no encontrado")
    subject = db.get(Subject, subject_id)
    if subject is None or subject.framework_id != plan.framework_id:
        raise ConflictError("El área no pertenece al marco curricular de esta planificación")
    unit = CurriculumUnit(version_id=ver.id, period_id=period.id, grade_id=grade_id, subject_id=subject.id,
                          title=title.strip(), sequence=sequence)
    db.add(unit)
    db.commit()
    return unit


def add_topic(db: Session, user: User, version_id: uuid.UUID, unit_id: uuid.UUID, competency_id: uuid.UUID,
              capacity_id: uuid.UUID | None, title: str, objective: str, sequence: int) -> CurriculumTopic:
    ver, _ = get_version(db, user, version_id)
    _require_draft(ver)
    unit = db.get(CurriculumUnit, unit_id)
    if unit is None or unit.version_id != ver.id:
        raise NotFoundError("Unidad no encontrada en esta versión")
    comp = db.get(Competency, competency_id)
    if comp is None or comp.subject_id != unit.subject_id:
        raise ConflictError("La competencia no pertenece al área de la unidad")
    if capacity_id is not None:
        cap = db.get(Capacity, capacity_id)
        if cap is None or cap.competency_id != comp.id:
            raise ConflictError("La capacidad no pertenece a la competencia")
    topic = CurriculumTopic(unit_id=unit.id, competency_id=comp.id, capacity_id=capacity_id, title=title.strip(),
                            learning_objective=objective.strip(), sequence=sequence)
    db.add(topic)
    db.commit()
    return topic


# ------------------------------------------------------------------ flujo de estados (humano en el bucle)
def submit(db: Session, user: User, version_id: uuid.UUID) -> CurriculumPlanVersion:
    ver, _ = get_version(db, user, version_id)
    _require_draft(ver)
    has_topic = db.scalar(select(CurriculumTopic.id).join(CurriculumUnit, CurriculumUnit.id == CurriculumTopic.unit_id)
                          .where(CurriculumUnit.version_id == ver.id).limit(1))
    if has_topic is None:
        raise ConflictError("La versión no tiene temas; nada que revisar")
    ver.status = "UNDER_REVIEW"
    db.commit()
    return ver


def _transition(db: Session, user: User, version_id: uuid.UUID, expected: str, new: str) -> CurriculumPlanVersion:
    ver, _ = get_version(db, user, version_id)
    if ver.status != expected:
        raise ConflictError(f"Transición inválida: la versión está en {ver.status}, se requiere {expected}")
    ver.status = new
    return ver


def reject(db: Session, admin: User, version_id: uuid.UUID) -> CurriculumPlanVersion:
    ver = _transition(db, admin, version_id, "UNDER_REVIEW", "DRAFT")
    db.commit()
    return ver


def approve(db: Session, admin: User, version_id: uuid.UUID) -> CurriculumPlanVersion:
    ver = _transition(db, admin, version_id, "UNDER_REVIEW", "APPROVED")
    ver.approved_by, ver.approved_at = admin.id, _now()
    db.commit()
    return ver


def activate(db: Session, admin: User, version_id: uuid.UUID) -> CurriculumPlanVersion:
    ver, _ = get_version(db, admin, version_id)
    if ver.status != "APPROVED":
        raise ConflictError(f"Solo se activa una versión APPROVED (actual: {ver.status})")
    # la anterior ACTIVE pasa a ARCHIVED (contenido intacto: las tareas históricas conservan su referencia)
    db.execute(update(CurriculumPlanVersion).where(CurriculumPlanVersion.plan_id == ver.plan_id,
                                                    CurriculumPlanVersion.status == "ACTIVE")
               .values(status="ARCHIVED"))
    db.flush()
    ver.status, ver.activated_at = "ACTIVE", _now()
    db.commit()
    return ver


def new_version(db: Session, user: User, plan_id: uuid.UUID) -> CurriculumPlanVersion:
    plan = get_plan(db, user, plan_id)
    versions = list(db.scalars(select(CurriculumPlanVersion).where(CurriculumPlanVersion.plan_id == plan.id)
                               .order_by(CurriculumPlanVersion.created_at)))
    if any(v.status in ("DRAFT", "UNDER_REVIEW") for v in versions):
        raise ConflictError("Ya existe una versión en borrador o revisión")
    base = next((v for v in versions if v.status == "ACTIVE"), versions[-1])
    year = db.get(AcademicYear, plan.academic_year_id).year  # type: ignore[union-attr]
    ver = CurriculumPlanVersion(plan_id=plan.id, label=f"{year}.{len(versions) + 1}", created_by=user.id)
    db.add(ver)
    db.flush()
    pmap: dict[uuid.UUID, uuid.UUID] = {}
    for p in db.scalars(select(AcademicPeriod).where(AcademicPeriod.version_id == base.id)):
        n = AcademicPeriod(version_id=ver.id, name=p.name, sequence=p.sequence, start_date=p.start_date,
                           end_date=p.end_date)
        db.add(n)
        db.flush()
        pmap[p.id] = n.id
    for u in db.scalars(select(CurriculumUnit).where(CurriculumUnit.version_id == base.id)):
        nu = CurriculumUnit(version_id=ver.id, period_id=pmap[u.period_id], grade_id=u.grade_id,
                            subject_id=u.subject_id, title=u.title, sequence=u.sequence)
        db.add(nu)
        db.flush()
        for t in db.scalars(select(CurriculumTopic).where(CurriculumTopic.unit_id == u.id)):
            db.add(CurriculumTopic(unit_id=nu.id, competency_id=t.competency_id, capacity_id=t.capacity_id,
                                   title=t.title, learning_objective=t.learning_objective, sequence=t.sequence))
    db.commit()
    return ver


# ------------------------------------------------------------------ lectura
def version_tree(db: Session, ver: CurriculumPlanVersion) -> dict:
    periods = []
    for p in db.scalars(select(AcademicPeriod).where(AcademicPeriod.version_id == ver.id)
                        .order_by(AcademicPeriod.sequence)):
        units = []
        for u in db.scalars(select(CurriculumUnit).where(CurriculumUnit.period_id == p.id)
                            .order_by(CurriculumUnit.grade_id, CurriculumUnit.sequence)):
            topics = [{"id": t.id, "title": t.title, "learning_objective": t.learning_objective,
                       "competency_id": t.competency_id, "capacity_id": t.capacity_id}
                      for t in db.scalars(select(CurriculumTopic).where(CurriculumTopic.unit_id == u.id)
                                          .order_by(CurriculumTopic.sequence))]
            units.append({"id": u.id, "title": u.title, "grade_id": u.grade_id, "subject_id": u.subject_id,
                          "topics": topics})
        periods.append({"id": p.id, "name": p.name, "sequence": p.sequence, "units": units})
    return {"id": ver.id, "plan_id": ver.plan_id, "label": ver.label, "status": ver.status, "periods": periods}


def list_plans(db: Session, user: User) -> list[dict]:
    q = select(SchoolCurriculumPlan)
    if user.role == Role.TEACHER:
        q = q.where(SchoolCurriculumPlan.school_id == teacher_school_id(db, user.id))
    out = []
    for plan in db.scalars(q.order_by(SchoolCurriculumPlan.created_at)):
        vers = db.scalars(select(CurriculumPlanVersion).where(CurriculumPlanVersion.plan_id == plan.id)
                          .order_by(CurriculumPlanVersion.created_at))
        out.append({"id": plan.id, "name": plan.name, "school_id": plan.school_id, "framework_id": plan.framework_id,
                    "versions": [{"id": v.id, "label": v.label, "status": v.status} for v in vers]})
    return out


def active_versions_for_school_year(db: Session, school_id: uuid.UUID, year: int) -> list[CurriculumPlanVersion]:
    return list(db.scalars(
        select(CurriculumPlanVersion).join(SchoolCurriculumPlan, SchoolCurriculumPlan.id == CurriculumPlanVersion.plan_id)
        .join(AcademicYear, AcademicYear.id == SchoolCurriculumPlan.academic_year_id)
        .where(SchoolCurriculumPlan.school_id == school_id, AcademicYear.year == year,
               CurriculumPlanVersion.status == "ACTIVE")))
