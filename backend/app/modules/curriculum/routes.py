import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.core.permissions import get_current_user, require_roles
from app.modules.curriculum.minedu_catalog import MINEDU_PRIMARY_SOURCES
from app.modules.curriculum.models import Capacity, Competency, CurriculumFramework, Grade, Subject
from app.modules.users.models import Role, User

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


class GradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    level: str
    number: int


@router.get("/grades", response_model=list[GradeOut])
def grades(db: Annotated[Session, Depends(get_db)],
           _: Annotated[User, Depends(get_current_user)]) -> list[Grade]:
    return list(db.scalars(select(Grade).order_by(Grade.level, Grade.number)))


@router.get("/minedu/primaria")
def minedu_primary_references(
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Read-only verified public MINEDU links: not a sync or framework activation."""
    return MINEDU_PRIMARY_SOURCES


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CompetencyIn(_Strict):
    code: str | None = Field(default=None, max_length=32)
    name: str = Field(min_length=2, max_length=300)
    capacities: list[Annotated[str, Field(min_length=2, max_length=300)]] = []


class SubjectIn(_Strict):
    name: str = Field(min_length=2, max_length=200)
    competencies: list[CompetencyIn] = Field(min_length=1)


class FrameworkIn(_Strict):
    country_code: str = Field(min_length=2, max_length=2)
    name: str = Field(min_length=2, max_length=200)
    version_label: str = Field(min_length=1, max_length=50)
    is_demo: bool  # obligatorio y explícito
    source_note: str | None = Field(default=None, max_length=2000)
    subjects: list[SubjectIn] = Field(min_length=1)


@router.post("/frameworks", status_code=201)
def import_framework(body: FrameworkIn, db: Annotated[Session, Depends(get_db)],
                     _: Annotated[User, Depends(require_roles(Role.ADMIN))]) -> dict:
    fw = CurriculumFramework(country_code=body.country_code.upper(), name=body.name,
                             version_label=body.version_label, is_demo=body.is_demo,
                             source_note=body.source_note)
    db.add(fw)
    try:
        db.flush()
        for s in body.subjects:
            subj = Subject(framework_id=fw.id, name=s.name)
            db.add(subj)
            db.flush()
            for c in s.competencies:
                comp = Competency(subject_id=subj.id, code=c.code, name=c.name)
                db.add(comp)
                db.flush()
                for cap in c.capacities:
                    db.add(Capacity(competency_id=comp.id, name=cap))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Marco curricular duplicado o con nombres repetidos") from exc
    return {"id": fw.id, "is_demo": fw.is_demo}


@router.get("/frameworks/{framework_id}")
def get_framework(framework_id: uuid.UUID, db: Annotated[Session, Depends(get_db)],
                  _: Annotated[User, Depends(get_current_user)]) -> dict:
    fw = db.get(CurriculumFramework, framework_id)
    if fw is None:
        raise NotFoundError("Marco curricular no encontrado")
    subjects = db.scalars(select(Subject).where(Subject.framework_id == fw.id).order_by(Subject.name))
    out = []
    for s in subjects:
        comps = []
        for c in db.scalars(select(Competency).where(Competency.subject_id == s.id).order_by(Competency.name)):
            caps = db.scalars(select(Capacity).where(Capacity.competency_id == c.id).order_by(Capacity.name))
            comps.append({"id": c.id, "code": c.code, "name": c.name,
                          "capacities": [{"id": k.id, "name": k.name} for k in caps]})
        out.append({"id": s.id, "name": s.name, "competencies": comps})
    return {"id": fw.id, "country_code": fw.country_code, "name": fw.name, "version_label": fw.version_label,
            "is_demo": fw.is_demo, "source_note": fw.source_note, "subjects": out}


@router.get("/frameworks")
def list_frameworks(db: Annotated[Session, Depends(get_db)],
                    _: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    return [{"id": f.id, "name": f.name, "version_label": f.version_label, "is_demo": f.is_demo}
            for f in db.scalars(select(CurriculumFramework).order_by(CurriculumFramework.name))]
