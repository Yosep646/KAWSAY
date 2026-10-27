import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from functools import cache

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O/1/I


@cache
def _hasher() -> PasswordHasher:
    if get_settings().app_env == "test":
        return PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)  # solo tests: rápido
    return PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher().hash(password)


def verify_password(hashed: str, password: str) -> bool:
    try:
        return _hasher().verify(hashed, password)
    except (VerificationError, InvalidHashError):
        return False


@cache
def _dummy_hash() -> str:
    return hash_password(secrets.token_urlsafe(16))


def burn_verification_time(password: str) -> None:
    """Igualar tiempos cuando el usuario no existe (evita enumeración por timing)."""
    verify_password(_dummy_hash(), password)


def create_access_token(user_id: uuid.UUID, role: str) -> tuple[str, int]:
    s = get_settings()
    now = datetime.now(UTC)
    ttl = timedelta(minutes=s.access_token_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "typ": "access", "jti": uuid.uuid4().hex,
               "iat": now, "exp": now + ttl, "iss": "kawsay"}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256"), int(ttl.total_seconds())


def decode_access_token(token: str) -> dict:
    try:
        data = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"], issuer="kawsay",
                          options={"require": ["exp", "sub", "typ", "iss"]})
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token inválido o expirado") from exc
    if data.get("typ") != "access":
        raise UnauthorizedError("Token inválido o expirado")
    return data


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_login_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))


def generate_pin() -> str:
    return f"{secrets.randbelow(10**6):06d}"
