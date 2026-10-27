"""AI Gateway: el dominio educativo NUNCA habla con un proveedor concreto; solo con esta interfaz.
Las API keys viven solo en el backend. Un proveedor caído no debe afectar login, offline, sync ni reglas."""
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

import httpx

from app.core.config import get_settings


class AIProviderError(Exception):
    pass


class AIUnavailable(AIProviderError):  # noqa: N818
    pass


class AITimeout(AIProviderError):  # noqa: N818
    pass


@dataclass(frozen=True)
class AIRequest:
    system: str
    user: str
    max_tokens: int = 2000


@dataclass(frozen=True)
class AIResponse:
    text: str
    provider: str
    model: str


class AIProvider(Protocol):
    name: str
    model: str

    def generate(self, req: AIRequest) -> AIResponse: ...


class DisabledProvider:
    name, model = "disabled", ""

    def generate(self, req: AIRequest) -> AIResponse:
        raise AIUnavailable("No hay proveedor de IA configurado (AI_PROVIDER=disabled)")


class AnthropicProvider:
    """Adaptador HTTP para la API de mensajes de Anthropic. UNVERIFIED-LIVE: no se probó contra el servicio real
    (requiere AI_API_KEY); el contrato HTTP sí está probado con un transporte simulado."""

    name = "anthropic"

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float, client: httpx.Client | None = None):
        self.model, self._key, self._url = model, api_key, base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)

    def generate(self, req: AIRequest) -> AIResponse:
        try:
            r = self._client.post(f"{self._url}/v1/messages", headers={
                "x-api-key": self._key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": self.model, "max_tokens": req.max_tokens, "system": req.system,
                      "messages": [{"role": "user", "content": req.user}]})
        except httpx.TimeoutException as exc:
            raise AITimeout("El proveedor de IA no respondió a tiempo") from exc
        except httpx.HTTPError as exc:
            raise AIUnavailable("No se pudo contactar al proveedor de IA") from exc
        if r.status_code in (429, 500, 502, 503, 504, 529):
            raise AIUnavailable(f"Proveedor de IA no disponible ({r.status_code})")
        if r.status_code != 200:
            raise AIProviderError(f"Error del proveedor de IA ({r.status_code})")  # sin volcar el cuerpo
        try:
            parts = r.json()["content"]
            text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            raise AIProviderError("Respuesta del proveedor con formato inesperado") from exc
        return AIResponse(text=text, provider=self.name, model=self.model)


class AIGateway:
    """Reintentos acotados + circuit breaker (evita tormentas de reintentos si el proveedor está caído)."""

    def __init__(self, provider: AIProvider, max_retries: int = 1, fail_threshold: int = 3, open_seconds: float = 30.0):
        self.provider, self.max_retries = provider, max_retries
        self._fails, self._open_until, self._threshold, self._open_seconds = 0, 0.0, fail_threshold, open_seconds

    @property
    def enabled(self) -> bool:
        return not isinstance(self.provider, DisabledProvider)

    def generate(self, req: AIRequest) -> AIResponse:
        if time.monotonic() < self._open_until:
            raise AIUnavailable("Circuito abierto: proveedor de IA temporalmente deshabilitado")
        last: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                out = self.provider.generate(req)
                self._fails = 0
                return out
            except (AIUnavailable, AITimeout) as exc:
                last = exc
        self._fails += 1
        if self._fails >= self._threshold:
            self._open_until = time.monotonic() + self._open_seconds
        assert last is not None
        raise last


@lru_cache
def get_gateway() -> AIGateway:
    s = get_settings()
    if s.ai_provider == "anthropic" and s.ai_api_key and s.ai_model:
        return AIGateway(AnthropicProvider(s.ai_api_key, s.ai_model, s.ai_base_url, s.ai_timeout_seconds))
    return AIGateway(DisabledProvider())
