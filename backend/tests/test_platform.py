import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


def test_request_id_generated_and_echoed(client: TestClient):
    assert len(client.get("/health").headers["X-Request-ID"]) >= 8
    r = client.get("/health", headers={"X-Request-ID": "trace-12345678"})
    assert r.headers["X-Request-ID"] == "trace-12345678"


def test_malicious_request_id_is_replaced(client: TestClient):
    r = client.get("/health", headers={"X-Request-ID": "bad\r\nvalue<script>"})
    assert "<" not in r.headers["X-Request-ID"]


def test_payload_limit(client: TestClient):
    r = client.post("/health", content=b"x" * 10, headers={"content-length": "999999999"})
    assert r.status_code == 413


def test_unhandled_error_hides_stacktrace():
    app = create_app()
    router = APIRouter()

    @router.get("/boom")
    def boom():
        raise RuntimeError("secreto-interno")

    app.include_router(router)
    r = TestClient(app, raise_server_exceptions=False).get("/boom")
    assert r.status_code == 500
    assert "secreto-interno" not in r.text and "Traceback" not in r.text
    assert r.json()["code"] == "internal_error" and r.json()["request_id"]


def test_security_headers(client: TestClient):
    h = client.get("/health").headers
    assert h["X-Content-Type-Options"] == "nosniff"


def test_production_requires_strong_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(app_env="production", database_url="sqlite:///x.db", jwt_secret="short")


def test_rejects_non_sqlite_database():
    with pytest.raises(ValidationError):
        Settings(database_url="postgresql://u:p@h/d")


def test_docs_disabled_in_production():
    s = Settings(app_env="production", database_url="sqlite:///x.db", jwt_secret="x" * 40)
    assert s.is_production
