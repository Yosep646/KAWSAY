import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import AppError

_hits: dict[str, deque[float]] = defaultdict(deque)


class TooManyRequests(AppError):
    status_code = 429
    code = "rate_limited"


def reset_rate_limits() -> None:
    _hits.clear()


def login_rate_limit(request: Request) -> None:
    """Ventana deslizante en memoria (por proceso). Deuda: mover a Redis con varios workers."""
    limit = get_settings().login_rate_limit_per_minute
    key = f"{request.url.path}:{request.client.host if request.client else 'unknown'}"
    now = time.monotonic()
    q = _hits[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise TooManyRequests("Demasiados intentos, espera un momento")
    q.append(now)


def check_rate(key: str, limit: int, window_seconds: int = 60) -> None:
    now = time.monotonic()
    q = _hits[key]
    while q and now - q[0] > window_seconds:
        q.popleft()
    if len(q) >= limit:
        raise TooManyRequests("Demasiadas solicitudes, espera un momento")
    q.append(now)
