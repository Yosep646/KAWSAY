"""SQLite como base de datos del servidor (decisión del autor: ADR-010).

Configuración para uso multiusuario modesto:
- WAL (lectores no bloquean al escritor), foreign_keys=ON, busy_timeout.
- Toda transacción usa BEGIN IMMEDIATE: un solo escritor a la vez y sin errores "database is locked" por
  promoción de lectura a escritura. Consecuencia: las peticiones NO deben mantener transacciones abiertas
  durante llamadas lentas (IA, webhooks); el código hace commit antes de ellas.
"""
import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _db_path(url: str) -> Path | None:
    database = make_url(url).database
    return None if not database or database == ":memory:" else Path(database)


def build_engine(url: str) -> Engine:
    path = _db_path(url)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 15}, pool_pre_ping=True)

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record):  # type: ignore[no-untyped-def]
        dbapi_conn.isolation_level = None  # las transacciones las controla SQLAlchemy (ver _on_begin)
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA busy_timeout=15000")
        cur.close()

    @event.listens_for(engine, "begin")
    def _on_begin(conn):  # type: ignore[no-untyped-def]
        conn.exec_driver_sql("BEGIN IMMEDIATE")

    if path is not None:
        path.touch(exist_ok=True)
        try:
            os.chmod(path, 0o600)  # solo el usuario del servicio puede leer la base (datos de menores)
        except OSError:
            pass  # Windows: permisos por ACL
    return engine


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        _engine = build_engine(get_settings().database_url)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def reset_engine() -> None:
    """Cierra el motor actual (cambio de base en pruebas / scripts)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine, _SessionLocal = None, None


def get_db() -> Iterator[Session]:
    get_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
