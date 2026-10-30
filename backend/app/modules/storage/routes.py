"""Estado verificable y exportación consistente de SQLite, solo para ADMIN.

El backup en memoria/temporal NO convierte Render Free en almacenamiento duradero.
El administrador debe descargarlo y guardarlo en un destino cifrado externo.
"""
import os
import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import _db_path, get_db
from app.core.permissions import require_roles
from app.modules.users.models import Role, User

router = APIRouter(prefix="/admin/storage", tags=["admin-storage"])
DB = Annotated[Session, Depends(get_db)]
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]


@router.get("/status")
def storage_status(db: DB, _: Admin) -> dict:
    """No afirmar persistencia hasta contar con un almacenamiento verificado."""
    try:
        db.execute(text("SELECT 1"))
        db.rollback()  # Evitar mantener un bloqueo de escritura en una ruta de lectura.
        database = "ok"
    except Exception:
        db.rollback()
        database = "unavailable"

    url = get_settings().database_url
    path = _db_path(url)
    exists = path is not None and path.is_file()
    return {
        "database": database,
        "engine": "SQLite",
        "manual_backup_available": database == "ok" and exists,
        "storage_persistence": "not_verified",
        "render_environment": os.getenv("RENDER", "").lower() == "true",
        "message": (
            "SQLite está accesible, pero no existe una verificación de durabilidad del almacenamiento. "
            "En Render Free se pierden los archivos locales al suspenderse, reiniciarse o desplegarse."
            if database == "ok" else
            "No se pudo comprobar la conexión con SQLite; no se puede exportar un respaldo."
        ),
    }


def _bytes(path: Path, temporary: tempfile.TemporaryDirectory[str]) -> Iterator[bytes]:
    try:
        with path.open("rb") as file:
            while block := file.read(1024 * 256):
                yield block
    finally:
        temporary.cleanup()


@router.get("/export")
def export_database(db: DB, _: Admin) -> StreamingResponse:
    """Descarga íntegra con SQLite online-backup API; incluye transacciones en WAL.

    El archivo temporal se elimina al terminar/cancelar la descarga. No incluye
    una función de restauración en caliente ni crea respaldos falsamente permanentes.
    """
    db.rollback()  # La autenticación consultó la BD; soltar su BEGIN IMMEDIATE.
    path = _db_path(get_settings().database_url)
    if path is None or not path.is_file():
        raise HTTPException(503, detail="La base SQLite no está disponible para respaldo.")

    temporary = tempfile.TemporaryDirectory(prefix="kawsay-sqlite-export-")
    backup_path = Path(temporary.name) / "snapshot.db"
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=15)) as source:
            with closing(sqlite3.connect(backup_path)) as destination:
                source.backup(destination)
                if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise sqlite3.DatabaseError("integrity_check falló")
                if destination.execute("PRAGMA foreign_key_check").fetchone() is not None:
                    raise sqlite3.DatabaseError("foreign_key_check falló")
    except (sqlite3.Error, OSError) as exc:
        temporary.cleanup()
        raise HTTPException(503, detail="No se pudo generar un respaldo SQLite íntegro.") from exc

    name = f"kawsay-respaldo-{datetime.now(UTC):%Y%m%d-%H%M%S}.db"
    return StreamingResponse(
        _bytes(backup_path, temporary),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{name}"',
            "Content-Length": str(backup_path.stat().st_size),
            "Cache-Control": "no-store, private",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )
