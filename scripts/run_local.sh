#!/usr/bin/env bash
# KAWSAY AI, servidor local (SQLite persistente en volumen Docker).
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v docker >/dev/null 2>&1; then echo "Instala Docker Desktop / Docker Engine." >&2; exit 1; fi
if [ ! -f .env ]; then
  python - <<'PYINNER'
from pathlib import Path
import secrets
Path('.env').write_text('JWT_SECRET='+secrets.token_hex(32)+'\nAPP_ENV=development\nWEB_BIND_IP=127.0.0.1\nAI_PROVIDER=disabled\n')
PYINNER
  chmod 600 .env 2>/dev/null || true
  echo "Se creó .env con JWT_SECRET aleatorio; no compartas el archivo."
fi
docker compose up -d --build backend teacher-web
echo 'Servidor web: http://127.0.0.1:8080'
echo 'Salud API: http://127.0.0.1:8080/health'
echo 'Para crear el primer administrador, ejecuta: docker compose exec -e ADMIN_PASSWORD=... backend python -m app.cli create-admin correo@ejemplo.pe "Administrador"'
echo 'Usa una contraseña fuerte y evita credenciales de ejemplo para datos reales.'
