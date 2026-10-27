# Infraestructura

- `docker-compose.yml` (raíz): backend + panel (nginx) + despachador opcional, con la base SQLite en un volumen. No verificado en el entorno de desarrollo.
- `teacher-web/nginx.conf`: CSP y proxy `/api`. `backend/Dockerfile`: usuario sin privilegios.
- Despliegue y recomendaciones: `docs/17-deployment.md`.
