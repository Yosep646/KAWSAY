from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    return app


app = create_app()
