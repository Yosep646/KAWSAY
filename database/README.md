# Base de datos: SQLite

El servidor guarda todo en **un archivo SQLite** (`backend/data/kawsay.db` por defecto; ver `DATABASE_URL`).
- Esquema y datos base (grados, idiomas) los crea la migración `backend/migrations/versions/*_0001_*.py` (`alembic upgrade head`).
- Modo WAL, claves foráneas activas, una sola escritura a la vez (`BEGIN IMMEDIATE`); `learning_attempts` es append-only (triggers).
- Respaldo consistente: `python scripts/dev.py backup` (o `python -m app.cli backup`). Verificación: `python -m app.cli check-db`.
- Para ver las tablas en VS Code: extensión «SQLite Viewer» / «SQLite» y abrir `backend/data/kawsay.db`.
- Diagrama ER y diseño: `docs/06-database-design.md` y `docs/07-er-diagram.md` (este último se genera desde los modelos).
- El archivo contiene datos de menores: no lo subas a Git ni lo compartas sin protegerlo (ver `docs/15-privacy.md`).
