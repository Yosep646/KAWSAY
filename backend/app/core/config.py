from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRETS = {"", "change-me", "changeme", "secret"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_name: str = "KAWSAY AI"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./data/kawsay.db"

    jwt_secret: str = ""
    login_rate_limit_per_minute: int = 10
    max_failed_logins: int = 5
    lockout_minutes: int = 15
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    cors_origins: str = ""  # lista separada por comas; vacío = ninguno
    max_request_bytes: int = 5_242_880  # 5 MB incl. metadata; curricular files limited to 4 MB

    # Reservados (fases posteriores)
    ml_allow_experimental: bool = False   # solo para demostraciones: permite usar un modelo CANDIDATE (siempre con advertencia)
    ai_provider: Literal["disabled", "anthropic"] = "disabled"
    ai_api_key: str = ""
    ai_model: str = ""
    ai_base_url: str = "https://api.anthropic.com"
    ai_timeout_seconds: float = 20.0
    automation_webhook_url: str = ""
    automation_webhook_secret: str = ""
    storage_endpoint: str = ""
    storage_bucket: str = ""
    redis_url: str = ""

    @field_validator("database_url")
    @classmethod
    def _driver(cls, v: str) -> str:
        if not v.startswith("sqlite"):
            raise ValueError("DATABASE_URL debe ser SQLite, p. ej. sqlite:///./data/kawsay.db (ver ADR-010)")
        return v

    @model_validator(mode="after")
    def _prod_checks(self) -> "Settings":
        if self.jwt_secret in _INSECURE_SECRETS or len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET debe tener >= 32 caracteres")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
