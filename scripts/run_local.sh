#!/usr/bin/env bash
# Alternativa con Docker. Lo más simple (sin Docker): python scripts/dev.py demo
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { printf "JWT_SECRET=%s\n" "$(openssl rand -hex 32)" > .env; echo ".env creado con un secreto aleatorio"; }
set -a; . ./.env; set +a
docker compose up -d --build
until curl -sf localhost:8000/ready >/dev/null; do sleep 2; done
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Kawsay-Demo-Local-2026}"
docker compose exec -T -e ADMIN_PASSWORD="$ADMIN_PASSWORD" backend python -m app.cli create-admin admin@demo.pe "Admin Demo" || true
pip install -q httpx
KAWSAY_URL=http://127.0.0.1:8000 KAWSAY_ADMIN_EMAIL=admin@demo.pe KAWSAY_ADMIN_PASSWORD="$ADMIN_PASSWORD" python scripts/demo_e2e.py
echo "Docs: http://127.0.0.1:8000/docs · Panel: http://127.0.0.1:8080"
