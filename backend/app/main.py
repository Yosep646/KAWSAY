import asyncio
import os
from contextlib import asynccontextmanager, suppress
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
from app.modules.curriculum.document_routes import router as curriculum_document_router
from app.modules.curriculum.routes import router as curriculum_router
from app.modules.health.routes import router as health_router
from app.modules.interventions.routes import router as interventions_router
from app.modules.languages.routes import router as languages_router
from app.modules.learning.routes import router as learning_router
from app.modules.planning.routes import router as planning_router
from app.modules.progress.routes import router as progress_router
from app.modules.schools.routes import router as schools_router
from app.modules.storage.routes import router as storage_router
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
        dispatch_task: asyncio.Task[None] | None = None
        # Opt-in: no modifica el comportamiento de las instalaciones existentes.
        # Un solo proceso despachador por base SQLite; n8n conserva el event_id
        # para evitar notificaciones duplicadas durante reintentos.
        if (settings.automation_auto_dispatch
                and settings.automation_webhook_url
                and settings.automation_webhook_secret):
            from app.workers.auto_dispatch import dispatch_loop

            dispatch_task = asyncio.create_task(
                dispatch_loop(settings.automation_dispatch_interval_seconds),
                name="kawsay-automation-dispatch",
            )
        try:
            yield
        finally:
            if dispatch_task is not None:
                dispatch_task.cancel()
                with suppress(asyncio.CancelledError):
                    await dispatch_task

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
              curriculum_router, curriculum_document_router, planning_router, assignments_router,
              sync_router, flags_router, interventions_router, analytics_router, progress_router,
              audit_router, automation_router, languages_router, tutor_router, learning_router,
              storage_router):
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
            # Vite copia teacher-web/public/* directamente a dist/.
            # Los fondos JPG/WEBP deben devolverse como IMAGEN, no index.html;
            # restringirlos a ficheros kawsay-* en la raíz para evitar acceso
            # a archivos internos, rutas arbitrarias y SVG ejecutable.
            public_static_files = {
                "sw.js", "startup-check.js", "favicon.ico",
                "manifest.webmanifest", "robots.txt",
            }
            image_media_types = {
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".webp": "image/webp",
                ".avif": "image/avif",
            }
            is_public_image = (
                requested_path.startswith("kawsay-")
                and "/" not in requested_path
                and "\\" not in requested_path
                and Path(requested_path).suffix.lower() in image_media_types
            )
            if requested_path in public_static_files or is_public_image:
                requested_file = dist / requested_path
                if not requested_file.is_file():
                    raise HTTPException(status_code=404, detail="Archivo estático no encontrado")
                return FileResponse(
                    requested_file,
                    media_type=image_media_types.get(requested_file.suffix.lower()),
                    headers={
                        "Cache-Control": "no-store",
                        "X-Content-Type-Options": "nosniff",
                    },
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
