"""Secure, bounded binary upload for curricular evidence documents.

Accepts DOCX/PDF as opaque attachments; never executes document contents,
never infers competencies or replaces an approved structured plan.
"""
import io
import uuid
import zipfile
from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, defer

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import require_roles
from app.modules.curriculum.document_models import CurriculumDocument
from app.modules.schools.models import School
from app.modules.teachers.models import TeacherProfile
from app.modules.users.models import Role, User

router = APIRouter(prefix="/curriculum/documents", tags=["curriculum-documents"])
DB = Annotated[Session, Depends(get_db)]
Staff = Annotated[User, Depends(require_roles(Role.ADMIN, Role.TEACHER))]
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]
MAX_UPLOAD = 4 * 1024 * 1024
AREA_OPTIONS = (
    "Matemática", "Comunicación", "Ciencia y Tecnología", "Personal Social",
    "Arte y Cultura", "Educación Física", "Inglés", "Educación Religiosa",
    "Tutoría", "Multigrado / General",
)


def school_for(db: Session, user: User, school_id: uuid.UUID) -> School:
    school = db.get(School, school_id)
    if school is None or school.deleted_at is not None:
        raise NotFoundError("Institución no encontrada")
    if user.role == Role.TEACHER:
        profile = db.get(TeacherProfile, user.id)
        if profile is None or profile.school_id != school_id:
            raise ForbiddenError("No tienes acceso a los archivos de esta institución")
    return school


def doc_info(record: CurriculumDocument) -> dict:
    return {
        "id": record.id, "school_id": record.school_id,
        "academic_year": record.academic_year, "education_level": record.education_level,
        "grade_number": record.grade_number, "area": record.area,
        "filename": record.filename, "file_size": record.file_size,
        "media_type": record.media_type, "status": record.status,
        "created_at": record.created_at, "uploaded_by": record.uploaded_by,
    }


def validate_payload(filename: str, body: bytes) -> tuple[str, str]:
    name = filename.strip()
    if not 1 <= len(name) <= 180 or "/" in name or "\\" in name or any(ord(c) < 32 for c in name):
        raise HTTPException(422, "Nombre de archivo inválido")
    if not body or len(body) > MAX_UPLOAD:
        raise HTTPException(413, "El archivo debe ocupar entre 1 byte y 4 MB")
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext == "pdf":
        if not body.startswith(b"%PDF-") or b"%%EOF" not in body[-2048:]:
            raise HTTPException(422, "El archivo no es un PDF válido")
        return name, "application/pdf"
    if ext == "docx":
        try:
            with zipfile.ZipFile(io.BytesIO(body)) as z:
                entries = z.infolist()
                names = {info.filename for info in entries}
                # Prevent ZIP bombs and office files with macros masquerading as docx.
                if (len(entries) > 1200 or sum(x.file_size for x in entries) > 24 * 1024 * 1024
                        or any(x.filename.startswith("/") or ".." in x.filename.split("/") for x in entries)
                        or "[Content_Types].xml" not in names or "word/document.xml" not in names
                        or any(x.lower().endswith("vbaproject.bin") for x in names)):
                    raise ValueError("DOCX no permitido")
        except (ValueError, zipfile.BadZipFile, OSError) as exc:
            raise HTTPException(422, "El archivo no es un Word DOCX válido") from exc
        return name, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    raise HTTPException(422, "Solo se admiten Word (.docx) y PDF (.pdf); no se admiten archivos .doc antiguos")


@router.get("/schools")
def document_schools(db: DB, user: Staff) -> list[dict]:
    if user.role == Role.ADMIN:
        rows = db.scalars(select(School).where(School.deleted_at.is_(None)).order_by(School.name)).all()
    else:
        profile = db.get(TeacherProfile, user.id)
        rows = [school_for(db, user, profile.school_id)] if profile else []
    return [{"id": r.id, "name": r.name} for r in rows]


@router.get("")
def list_documents(db: DB, user: Staff,
                   school_id: uuid.UUID,
                   academic_year: Annotated[int, Query(ge=2020, le=2100)],
                   education_level: Annotated[str, Query(pattern="^(PRIMARIA|SECUNDARIA)$")],
                   grade_number: Annotated[int, Query(ge=1, le=6)]) -> list[dict]:
    school_for(db, user, school_id)
    if education_level == "SECUNDARIA" and grade_number > 5:
        raise HTTPException(422, "Secundaria comprende del 1.º al 5.º grado")
    docs = db.scalars(select(CurriculumDocument).where(
        CurriculumDocument.school_id == school_id,
        CurriculumDocument.academic_year == academic_year,
        CurriculumDocument.education_level == education_level,
        CurriculumDocument.grade_number == grade_number,
    ).options(defer(CurriculumDocument.file_data)).order_by(CurriculumDocument.created_at.desc(),CurriculumDocument.id.desc()).limit(150)).all()
    return [doc_info(x) for x in docs]


@router.post("", status_code=201)
async def upload_document(request: Request, db: DB, user: Staff,
                          school_id: uuid.UUID, academic_year: Annotated[int, Query(ge=2020, le=2100)],
                          education_level: Annotated[str, Query(pattern="^(PRIMARIA|SECUNDARIA)$")],
                          grade_number: Annotated[int, Query(ge=1, le=6)],
                          area: Annotated[str, Query(min_length=2, max_length=80)],
                          filename: Annotated[str, Query(min_length=1, max_length=180)]) -> dict:
    school_for(db, user, school_id)
    if education_level == "SECUNDARIA" and grade_number > 5:
        raise HTTPException(422, "Secundaria comprende del 1.º al 5.º grado")
    if area not in AREA_OPTIONS:
        raise HTTPException(422, "El área curricular no está en el catálogo")
    # Middleware enforces Content-Length for all mutations and a 5 MB ceiling.
    if request.headers.get("content-type", "").split(";")[0].lower() != "application/octet-stream":
        raise HTTPException(415, "El archivo debe enviarse como contenido binario")
    if int(request.headers.get("content-length", "0") or "0") > MAX_UPLOAD:
        raise HTTPException(413, "Tamaño máximo: 4 MB")
    payload = await request.body()
    safe_name, mime = validate_payload(filename, payload)
    document = CurriculumDocument(
        school_id=school_id, uploaded_by=user.id, education_level=education_level,
        grade_number=grade_number, academic_year=academic_year, area=area,
        filename=safe_name, media_type=mime, file_size=len(payload),
        file_data=payload, status="PENDING",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return doc_info(document)


@router.get("/{document_id}/download")
def download_document(document_id: uuid.UUID, db: DB, user: Staff) -> Response:
    document = db.get(CurriculumDocument, document_id)
    if document is None:
        raise NotFoundError("Documento no encontrado")
    school_for(db, user, document.school_id)
    # Restrict output to download; docx/pdf cannot run in the app origin.
    return Response(
        content=document.file_data, media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(document.filename)}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )


@router.post("/{document_id}/review")
def review_document(document_id: uuid.UUID, db: DB, admin: Admin,
                    approved: bool = Query()) -> dict:
    document = db.get(CurriculumDocument, document_id)
    if document is None:
        raise NotFoundError("Documento no encontrado")
    document.status = "APPROVED" if approved else "REJECTED"
    document.reviewed_by = admin.id
    document.reviewed_at = datetime.now(UTC)
    db.commit()
    return doc_info(document)
