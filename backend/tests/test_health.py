from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import get_engine


def test_health_ok(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_ok_with_database(client: TestClient):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "checks": {"database": "ok"}}


def test_ready_503_when_database_down(monkeypatch):
    from app.core import database
    from app.main import create_app

    class Boom:
        def execute(self, *_a, **_k):
            raise RuntimeError("db down")

    app = create_app()
    app.dependency_overrides[database.get_db] = lambda: Boom()
    r = TestClient(app).get("/ready")
    assert r.status_code == 503
    assert r.json()["checks"]["database"] == "unavailable"
    assert "db down" not in r.text  # no filtrar detalles internos


def test_migrations_applied():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    head = ScriptDirectory.from_config(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))).get_current_head()
    with get_engine().connect() as c:
        assert c.execute(text("SELECT version_num FROM alembic_version")).scalar() == head
