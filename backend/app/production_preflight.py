"""Preflight fail-closed for SQLite on a Render *persistent disk*.

Default demo mode preserves existing behavior and never claims durability.
Persistent mode refuses to boot against an empty/ephemeral location, so a
deployment cannot silently create a new database and hide existing records.
"""
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from app.core.config import get_settings
from app.core.database import _db_path


class StorageNotReady(RuntimeError):
    pass


def check_storage(mode: str, database_url: str, mount_path: str,
                  *, render: bool, is_mount: bool | None = None) -> dict[str, str]:
    if mode not in {"demo", "persistent"}:
        raise StorageNotReady("KAWSAY_STORAGE_MODE debe ser 'demo' o 'persistent'")

    path = _db_path(database_url)
    if path is None:
        raise StorageNotReady("Se requiere un archivo SQLite en disco para desplegar KAWSAY")

    if mode == "demo":
        # Nunca afirmar durabilidad de una SQLite dentro de un contenedor Free.
        return {
            "mode": "demo",
            "result": "ephemeral_database_not_guaranteed",
            "warning": "No guardar datos escolares reales en este servicio sin disco persistente.",
        }

    mount = Path(mount_path).resolve()
    if not Path(mount_path).is_absolute() or mount == Path("/"):
        raise StorageNotReady("KAWSAY_PERSISTENT_MOUNT debe ser una ruta absoluta de disco distinta de /")
    if render and not (mount.is_mount() if is_mount is None else is_mount):
        raise StorageNotReady("No se detecta un disco persistente Render en KAWSAY_PERSISTENT_MOUNT")

    target = path.resolve()
    try:
        relative = target.relative_to(mount)
    except ValueError as exc:
        raise StorageNotReady("DATABASE_URL debe apuntar dentro del disco persistente") from exc
    if not relative.parts:
        raise StorageNotReady("DATABASE_URL debe apuntar a un archivo bajo el punto de montaje")

    # Fail-closed. Never allow Alembic to create a blank DB during cutover.
    if not path.is_file():
        raise StorageNotReady(
            "No se encontró la base restaurada en el disco persistente. "
            "Restaura una copia SQLite validada ANTES de desplegar."
        )

    try:
        with closing(sqlite3.connect(target.as_uri() + "?mode=ro", uri=True, timeout=10)) as con:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise StorageNotReady("La base restaurada no supera integrity_check")
            if con.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise StorageNotReady("La base restaurada tiene claves foráneas inválidas")
            tables = {row[0] for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
            if not {"alembic_version", "users", "schools"}.issubset(tables):
                raise StorageNotReady(
                    "El archivo existe pero no tiene el esquema esperado de KAWSAY")
    except (OSError, sqlite3.DatabaseError) as exc:
        raise StorageNotReady("No se pudo abrir y verificar la base SQLite restaurada") from exc

    return {
        "mode": "persistent",
        "result": "mounted_database_verified",
        "database": str(target),
        "warning": "Montaje y contenido verificados; comprobar también respaldo externo y reinicio real.",
    }


def main() -> int:
    settings = get_settings()
    try:
        status = check_storage(
            os.getenv("KAWSAY_STORAGE_MODE", "demo").strip().lower(),
            settings.database_url,
            os.getenv("KAWSAY_PERSISTENT_MOUNT", "/var/data"),
            render=os.getenv("RENDER", "").lower() == "true",
        )
    except StorageNotReady as exc:
        print(f"KAWSAY almacenamiento NO listo: {exc}", file=sys.stderr)
        return 2
    print("KAWSAY almacenamiento:", status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
