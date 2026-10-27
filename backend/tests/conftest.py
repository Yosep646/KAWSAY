# ruff: noqa: E402
import os
import shutil
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # raíz del repo: permite importar `ml` en las pruebas
_TMP = Path(tempfile.mkdtemp(prefix="kawsay_tests_"))
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'bootstrap.db'}"
os.environ.setdefault("JWT_SECRET", "test_secret_test_secret_test_secret_123456")
os.environ["LOGIN_RATE_LIMIT_PER_MINUTE"] = "1000"

import uuid

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import reset_engine
from app.core.rate_limit import reset_rate_limits
from app.main import create_app
from app.models_registry import *  # noqa: F403
from app.modules.schools.models import School
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_staff_user

PW = "una-clave-larga-123"


_TEMPLATE = _TMP / "template.db"


@pytest.fixture(scope="session", autouse=True)
def _migrated_template():
    """Migra UNA vez una base plantilla; cada prueba trabaja sobre su propia copia (aislamiento total)."""
    get_settings().database_url = f"sqlite:///{_TEMPLATE}"
    reset_engine()
    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    reset_engine()
    with closing(sqlite3.connect(_TEMPLATE)) as raw:   # deja un único archivo (sin -wal) para copiarlo
        raw.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    yield
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path):
    path = tmp_path / "test.db"
    shutil.copy(_TEMPLATE, path)
    get_settings().database_url = f"sqlite:///{path}"
    reset_engine()
    reset_rate_limits()
    get_settings().login_rate_limit_per_minute = 1000
    yield
    reset_engine()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(), raise_server_exceptions=False)


@pytest.fixture
def db():
    """Sesión de PRUEBA en autocommit: lee siempre datos frescos y nunca retiene el bloqueo de escritura del servidor."""
    engine = create_engine(get_settings().database_url, connect_args={"check_same_thread": False, "timeout": 15})

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _rec):
        dbapi_conn.isolation_level = None
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
        dbapi_conn.execute("PRAGMA busy_timeout=15000")

    with Session(engine, expire_on_commit=False) as s:
        yield s
    engine.dispose()


class World:
    """Helpers de prueba (los usuarios se crean vía servicios, no hay usuarios por defecto)."""

    def __init__(self, client: TestClient, db: Session):
        self.c, self.db = client, db

    @property
    def app(self):
        return self.c.app

    def school(self, name="Escuela Demo") -> School:
        s = School(name=name)
        self.db.add(s)
        self.db.commit()
        return s

    def staff(self, role: str, email: str, school: School | None = None):
        return create_staff_user(self.db, UserCreate(role=role, email=email, password=PW,
                                                     display_name=email.split("@")[0],
                                                     school_id=school.id if school else None))

    def login(self, email: str) -> dict:
        r = self.c.post("/api/v1/auth/login", json={"email": email, "password": PW})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def grade_id(self, headers, number: int, level="PRIMARIA") -> int:
        rows = self.c.get("/api/v1/curriculum/grades", headers=headers).json()
        return next(g["id"] for g in rows if g["number"] == number and g["level"] == level)

    def classroom(self, headers, name="Aula Multigrado") -> str:
        r = self.c.post("/api/v1/classrooms", json={"name": name, "academic_year": 2026}, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def student(self, headers, classroom_id, grade, name="Ana") -> dict:
        r = self.c.post("/api/v1/students", headers=headers, json={
            "display_name": name, "grade_id": self.grade_id(headers, grade), "classroom_id": classroom_id})
        assert r.status_code == 201, r.text
        return r.json()


@pytest.fixture
def w(client, db) -> World:
    return World(client, db)


def new_device() -> str:
    return str(uuid.uuid4())
