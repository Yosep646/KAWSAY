"""Utilidades de administración.
  ADMIN_PASSWORD=... python -m app.cli create-admin correo@dominio "Nombre"   (no existen usuarios por defecto)
  python -m app.cli backup [carpeta] [copias_a_conservar]                      (copia consistente de la base SQLite)
  python -m app.cli check-db                                                    (integridad + claves foráneas)
"""
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


def check_db() -> dict:
    path = _db_path(get_settings().database_url)
    if path is None:
        raise SystemExit("Base de datos no encontrada")
    with closing(sqlite3.connect(path)) as c:
        return {"integrity": c.execute("PRAGMA integrity_check").fetchone()[0],
                "foreign_key_violations": len(c.execute("PRAGMA foreign_key_check").fetchall()),
                "journal_mode": c.execute("PRAGMA journal_mode").fetchone()[0]}


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
    if cmd == "check-db":
        res = check_db()
        print(res)
        return 0 if res["integrity"] == "ok" and res["foreign_key_violations"] == 0 else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
