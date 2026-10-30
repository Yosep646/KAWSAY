import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.logging import request_id_ctx

log = logging.getLogger("kawsay.access")
_SAFE_ID = re.compile(r"^[A-Za-z0-9_\-]{8,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Request-ID/correlation-ID, log de acceso y límite de payload."""

    def __init__(self, app, max_request_bytes: int):
        super().__init__(app)
        self.max_bytes = max_request_bytes

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_ctx.set(rid)
        start = time.perf_counter()
        try:
            length = request.headers.get("content-length")
            chunked = "chunked" in request.headers.get("transfer-encoding", "").lower()
            if request.method in ("POST", "PUT", "PATCH") and (chunked or (length is not None and not length.isdigit())):
                # Sin Content-Length verificable no se puede limitar el tamaño: se rechaza (los clientes legítimos lo envían)
                response: Response = JSONResponse(
                    {"code": "length_required", "message": "Content-Length requerido", "request_id": rid}, status_code=411)
            elif length and length.isdigit() and int(length) > self.max_bytes:
                response = JSONResponse(
                    {"code": "payload_too_large", "message": "Payload demasiado grande", "request_id": rid},
                    status_code=413,
                )
            else:
                response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
            response.headers["Cross-Origin-Resource-Policy"] = "same-site"
            if not request.url.path.startswith(("/docs", "/openapi")):   # Swagger UI necesita sus propios recursos
                response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
            if get_settings().is_production:
                response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
            elapsed = round((time.perf_counter() - start) * 1000, 1)
            log.info(
                "request",
                extra={"extra_fields": {"method": request.method, "path": request.url.path,
                                         "status": response.status_code, "ms": elapsed}},
            )
            return response
        finally:
            request_id_ctx.reset(token)
