"""Pruebas de persistencia local: escritura HTTP, nuevo motor y lectura durable."""
from pathlib import Path
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import cli
from app.core.config import get_settings
from app.core.database import get_engine, reset_engine
from app.modules.classrooms.models import Classroom


def test_classroom_saved_via_api_survives_database_engine_restart(w):
    school = w.school("Escuela Persistencia Local")
    w.staff("TEACHER", "persistencia@kawsay.com", school)
    teacher = w.login("persistencia@kawsay.com")
    classroom_id = w.classroom(teacher, name="Aula que debe conservarse")

    # Se cierran las conexiones existentes de la aplicación, como en un reinicio.
    reset_engine()
    with Session(get_engine()) as db:
        room = db.scalar(select(Classroom).where(Classroom.id == uuid.UUID(classroom_id)))
        assert room is not None
        assert room.name == "Aula que debe conservarse"

    # La misma API recupera el registro guardado, no un estado temporal de React.
    response = w.c.get(f"/api/v1/classrooms/{classroom_id}", headers=teacher)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Aula que debe conservarse"

    status = cli.db_status()
    assert Path(status["path"]).is_file()
    assert status["records"]["classrooms"] >= 1
    assert status["migration_version"]
    assert status["integrity"] == "ok"
    assert status["foreign_key_violations"] == 0
    # La comprobación local no demuestra que Render tenga disco persistente.
    assert status["storage_persistence"] == "not_verified"


def test_missing_database_diagnostic_does_not_create_empty_file(monkeypatch, tmp_path):
    missing = tmp_path / "missing" / "kawsay.db"
    monkeypatch.setattr(get_settings(), "database_url", f"sqlite:///{missing}")
    with pytest.raises(SystemExit, match="No se encontró la base de datos"):
        cli.check_db()
    with pytest.raises(SystemExit, match="No se encontró la base de datos"):
        cli.db_status()
    assert not missing.exists()  # ningún diagnóstico crea una base vacía


def test_dev_run_migrates_before_starting(monkeypatch, tmp_path):
    from scripts import dev

    python = tmp_path / "python.exe"
    python.touch()
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / ".env").write_text("DATABASE_URL=sqlite:///./data/kawsay.db\n", encoding="utf-8")
    monkeypatch.setattr(dev, "PY", python)
    monkeypatch.setattr(dev, "BACKEND", backend)
    commands = []

    def fake_run(cmd, cwd=None, **_kwargs):
        commands.append((list(map(str, cmd)), cwd))
        return 0

    monkeypatch.setattr(dev, "run", fake_run)
    dev.ensure_database_ready()
    assert len(commands) == 2
    assert commands[0][0][-3:] == ["alembic", "upgrade", "head"]
    assert commands[1][0][-2:] == ["app.cli", "db-status"]
    assert all(cwd == backend for _, cwd in commands)
