import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.modules.analytics.routes import router as analytics_router
from app.modules.assignments.routes import router as assignments_router
from app.modules.audit.routes import router as audit_router
from app.modules.auth.routes import router as auth_router
from app.modules.automation.routes import router as automation_router
from app.modules.classrooms.routes import router as classrooms_router
from app.modules.curriculum.routes import router as curriculum_router
from app.modules.health.routes import router as health_router
from app.modules.interventions.routes import router as interventions_router
from app.modules.languages.routes import router as languages_router
from app.modules.learning.routes import router as learning_router
from app.modules.planning.routes import router as planning_router
from app.modules.progress.routes import router as progress_router
from app.modules.schools.routes import router as schools_router
from app.modules.students.routes import router as students_router
from app.modules.support_flags.routes import router as flags_router
from app.modules.sync.routes import router as sync_router
from app.modules.tutor.routes import router as tutor_router
from app.modules.users.routes import router as users_router

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    app.add_middleware(RequestContextMiddleware, max_request_bytes=settings.max_request_bytes)
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,  # lista blanca explícita, nunca "*"
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Idempotency-Key"],
        )
    register_exception_handlers(app)

    # Sondas operativas (sin versionar: las usan orquestadores)
    app.include_router(health_router)
    api = APIRouter(prefix=API_PREFIX)
    for r in (auth_router, users_router, schools_router, classrooms_router, students_router,
              curriculum_router, planning_router, assignments_router,
              sync_router, flags_router, interventions_router, analytics_router, progress_router,
              audit_router, automation_router, languages_router, tutor_router, learning_router):
        api.include_router(r)
    app.include_router(api)

    # Modo despliegue monolítico: el frontend compilado se publica desde FastAPI.
    # Deshabilitado por defecto para no alterar las pruebas ni el despliegue local Nginx.
    web_dist = os.environ.get("KAWSAY_SERVE_WEB_DIR", "").strip()
    if web_dist:
        dist = Path(web_dist).resolve()
        index = dist / "index.html"
        if not index.is_file():
            raise RuntimeError(f"Falta frontend compilado: {index}")
        if (dist / "assets").is_dir():
            app.mount("/assets", StaticFiles(directory=dist / "assets"), name="web_assets")

        @app.get("/{requested_path:path}", include_in_schema=False)
        def serve_web(requested_path: str):
            if requested_path.startswith(("api/", "docs", "openapi", "ready", "health")):
                raise HTTPException(status_code=404)
            # Vite copia los archivos de public/ a la raíz de dist/.
            # El banner utiliza esta foto local: debe servirse como JPEG,
            # nunca como fallback HTML del SPA (evita un fondo invisible).
            public_static_files = {
                "sw.js", "startup-check.js", "favicon.ico",
                "manifest.webmanifest", "robots.txt", "kawsay-hero-rural.jpg",
                "kawsay-diversidad-fondo.jpg",
                "kawsay-login-encuadre-desktop.jpg",
                "kawsay-login-encuadre-mobile.jpg",
            }
            if requested_path in public_static_files:
                requested_file = dist / requested_path
                if not requested_file.is_file():
                    raise HTTPException(status_code=404, detail="Archivo estático no encontrado")
                return FileResponse(
                    requested_file,
                    media_type="image/jpeg" if requested_path in {
                        "kawsay-hero-rural.jpg", "kawsay-diversidad-fondo.jpg",
                        "kawsay-login-encuadre-desktop.jpg",
                        "kawsay-login-encuadre-mobile.jpg"
                    } else None,
                    headers={"Cache-Control": "no-store"},
                )
            return FileResponse(index, media_type="text/html", headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": (
                 "default-src 'self'; script-src 'self'; "
                 "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                 "font-src 'self' data:; connect-src 'self'; object-src 'none'; "
                 "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
                ),
            })
    return app


app = create_app()
