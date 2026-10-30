"""Utilidades de administración.
  ADMIN_PASSWORD=... python -m app.cli create-admin correo@dominio "Nombre"   (no existen usuarios por defecto)
  python -m app.cli backup [carpeta] [copias_a_conservar]                      (copia consistente de la base SQLite)
  python -m app.cli check-db                                                    (integridad + claves foráneas)
  python -m app.cli db-status                                                   (ruta exacta + conteos, solo lectura)
"""
import json
import os
import sqlite3
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import _db_path, get_engine
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_staff_user


def backup(dest_dir: str = "backups", keep: int = 14) -> Path:
    """Copia en caliente con la API de backup de SQLite (consistente aunque haya usuarios conectados)."""
    src = _db_path(get_settings().database_url)
    if src is None or not src.exists():
        raise SystemExit("No se encontró la base de datos")
    out_dir = Path(dest_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"kawsay-{datetime.now(UTC):%Y%m%d-%H%M%S-%f}.db"
    with closing(sqlite3.connect(src)) as s, closing(sqlite3.connect(dest)) as d:
        s.backup(d)
        if d.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            dest.unlink(missing_ok=True)
            raise SystemExit("La copia no pasó la verificación de integridad")
    try:
        os.chmod(dest, 0o600)
    except OSError:
        pass
    for old in sorted(out_dir.glob("kawsay-*.db"))[:-keep]:
        old.unlink(missing_ok=True)
    return dest


def _existing_database_path() -> Path:
    """Nunca abrir SQLite en modo creación al diagnosticar la base."""
    path = _db_path(get_settings().database_url)
    if path is None or not path.is_file():
        raise SystemExit("No se encontró la base de datos SQLite configurada; ejecuta setup antes de iniciar.")
    return path.resolve()


def _read_only_connection(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)


def check_db() -> dict:
    path = _existing_database_path()
    with closing(_read_only_connection(path)) as c:
        return {"integrity": c.execute("PRAGMA integrity_check").fetchone()[0],
                "foreign_key_violations": len(c.execute("PRAGMA foreign_key_check").fetchall()),
                "journal_mode": c.execute("PRAGMA journal_mode").fetchone()[0]}


def db_status() -> dict:
    """Ruta real y conteos sin exponer información personal; la lectura no crea archivos."""
    path = _existing_database_path()
    check = check_db()
    with closing(_read_only_connection(path)) as c:
        tables = {row[0] for row in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        version = c.execute("SELECT version_num FROM alembic_version").fetchone()[0] \
            if "alembic_version" in tables else None
        names = ("schools", "classrooms", "student_profiles", "assignments",
                 "student_assignments", "curriculum_documents")
        counts = {name: int(c.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
                  for name in names if name in tables}
    return {
        "database": "sqlite",
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "migration_version": version,
        "tables_present": len(tables),
        "records": counts,
        "integrity": check["integrity"],
        "foreign_key_violations": check["foreign_key_violations"],
        "storage_persistence": "not_verified",
        "note": ("Los registros sobreviven a reinicios si este archivo permanece en un disco persistente. "
                 "Render Free no conserva SQLite dentro del contenedor; no usarlo para datos reales."),
    }


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "create-admin" and len(sys.argv) == 4:
        with Session(get_engine()) as db:
            user = create_staff_user(db, UserCreate(role="ADMIN", email=sys.argv[2], password=os.environ.get("ADMIN_PASSWORD", ""),
                                                    display_name=sys.argv[3]))
            print(f"Administrador creado: {user.id}")
        return 0
    if cmd == "backup":
        folder = sys.argv[2] if len(sys.argv) > 2 else "backups"
        keep = int(sys.argv[3]) if len(sys.argv) > 3 else 14
        print("Copia creada:", backup(folder, keep))
        return 0
    if cmd == "db-status":
        info = db_status()
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0 if info["integrity"] == "ok" and info["foreign_key_violations"] == 0 and info["migration_version"] else 1
    if cmd == "check-db":
        res = check_db()
        print(res)
        return 0 if res["integrity"] == "ok" and res["foreign_key_violations"] == 0 else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
