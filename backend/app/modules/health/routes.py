from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db

router = APIRouter(tags=["ops"])


@router.get("/health", summary="Liveness: el proceso responde")
def health() -> dict:
    s = get_settings()
    return {"status": "ok", "service": s.app_name, "version": s.app_version}


@router.get("/ready", summary="Readiness: dependencias disponibles")
def ready(db: Annotated[Session, Depends(get_db)]) -> JSONResponse:
    checks: dict[str, str] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    ok = all(v == "ok" for v in checks.values())
    return JSONResponse({"status": "ready" if ok else "not_ready", "checks": checks},
                        status_code=200 if ok else 503)
