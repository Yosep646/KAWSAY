"""Comprobar que no se puede activar Render persistente sin copia restaurada."""
import sqlite3
from pathlib import Path

import pytest

from app.production_preflight import StorageNotReady, check_storage


def db_with_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.executescript("""
            CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY);
            INSERT INTO alembic_version VALUES ('0001');
            CREATE TABLE users (id TEXT PRIMARY KEY);
            CREATE TABLE schools (id TEXT PRIMARY KEY);
        """)


def test_demo_mode_explains_ephemeral_storage(tmp_path: Path) -> None:
    result = check_storage(
        "demo", f"sqlite:///{tmp_path / 'missing.db'}",
        str(tmp_path), render=True, is_mount=False,
    )
    assert result["result"] == "ephemeral_database_not_guaranteed"
    assert not (tmp_path / "missing.db").exists()


def test_persistent_missing_disk_is_blocked(tmp_path: Path) -> None:
    path = tmp_path / "disk" / "kawsay.db"
    db_with_schema(path)
    with pytest.raises(StorageNotReady, match="disco persistente"):
        check_storage("persistent", f"sqlite:///{path}", str(path.parent),
                      render=True, is_mount=False)


def test_persistent_refuses_empty_database_without_restoration(tmp_path: Path) -> None:
    mount = tmp_path / "disk"
    mount.mkdir()
    missing = mount / "kawsay.db"
    with pytest.raises(StorageNotReady, match="Restaura una copia"):
        check_storage("persistent", f"sqlite:///{missing}", str(mount),
                      render=True, is_mount=True)
    assert not missing.exists()  # jamás crear una SQLite nueva por comprobar


def test_persistent_refuses_wrong_mount_path(tmp_path: Path) -> None:
    mount = tmp_path / "disk"
    other = tmp_path / "ephemeral" / "kawsay.db"
    db_with_schema(other)
    with pytest.raises(StorageNotReady, match="dentro del disco persistente"):
        check_storage("persistent", f"sqlite:///{other}", str(mount),
                      render=True, is_mount=True)


def test_persistent_refuses_corrupt_file_and_wrong_schema(tmp_path: Path) -> None:
    mount = tmp_path / "disk"
    mount.mkdir()
    db = mount / "kawsay.db"
    db.write_bytes(b"contenido no SQLite")
    with pytest.raises(StorageNotReady, match="No se pudo abrir"):
        check_storage("persistent", f"sqlite:///{db}", str(mount),
                      render=True, is_mount=True)
    db.unlink()
    with sqlite3.connect(db) as con:
        con.execute("CREATE TABLE other_table (id INTEGER)")
    with pytest.raises(StorageNotReady, match="esquema esperado"):
        check_storage("persistent", f"sqlite:///{db}", str(mount),
                      render=True, is_mount=True)


def test_persistent_valid_database_is_accepted(tmp_path: Path) -> None:
    mount = tmp_path / "disk"
    db = mount / "kawsay.db"
    db_with_schema(db)
    status = check_storage("persistent", f"sqlite:///{db}", str(mount),
                           render=True, is_mount=True)
    assert status["result"] == "mounted_database_verified"
    assert status["database"] == str(db)
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0001"
