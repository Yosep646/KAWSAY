# Isolated demonstration. SQLite is ephemeral on the Free plan.
FROM node:24-alpine AS web-build
WORKDIR /web
COPY teacher-web/package*.json ./
RUN npm ci --no-audit --no-fund
COPY teacher-web/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
RUN addgroup --system kawsay && adduser --system --ingroup kawsay kawsay
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web-build /web/dist/ /srv/web-dist/
RUN mkdir -p /srv/data && chown -R kawsay:kawsay /srv
USER kawsay
ENV KAWSAY_SERVE_WEB_DIR=/srv/web-dist
EXPOSE 10000
CMD ["sh", "-c", "alembic upgrade head && python -m app.demo_bootstrap && exec uvicorn app.deploy:application --factory --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]
