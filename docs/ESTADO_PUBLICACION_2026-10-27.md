# Estado de publicación a GitHub y Render (27/10/2026)

## Resultado

- **GitHub:** no se ha subido esta nueva versión. Se intentó crear la rama `deploy/kawsay-demo-20261027` mediante la conexión GitHub y respondió `403 Resource not accessible by integration`. El repositorio de origen sigue sin modificaciones.
- **Render:** no se ha creado ni reemplazado ningún servicio. Los anteriores servicios KAWSAY siguen vinculados a otra estructura del repositorio `alcides18huerto-svg/-KAWSAY-AI`.
- **Nuevo paquete:** `render.Dockerfile`, `render.yaml`, `.dockerignore`, una ruta opcional para servir React con FastAPI, documentación y `scripts/publicar_en_github.ps1`.

## Pruebas nuevas completadas

- `python -m pytest tests/test_render_spa.py tests/test_auth.py tests/test_assignments.py tests/test_sync_reto10.py -q` → **39 aprobadas**, incluyendo rutas de administrador, docente, estudiante, Service Worker, recursos estáticos y aislamiento de `/api/`.
- Compilación sintáctica del código backend → satisfactoria.
- No se pudo ejecutar `npm ci`/`vite build` ni construir la imagen Docker en este entorno; tampoco se ha verificado el funcionamiento offline E2E.

## Bloqueos y riesgos

1. La integración GitHub carece de permiso para escribir la rama de despliegue, aunque el repositorio sea visible. Autoriza escritura en GitHub o ejecuta el script PowerShell incluido desde una sesión con permisos.
2. El backend actual sólo admite **SQLite**; Render Free proporciona almacenamiento efímero. El despliegue previsto es **una demostración con datos ficticios**. No alojar información real de menores ni anunciar persistencia garantizada.
3. El Dockerfile depende de la instalación online de npm y pip durante la compilación en Render. Debe comprobarse el build real.
4. Al publicar el proyecto, configura `JWT_SECRET` seguro en el panel privado de Render y verifica `/health`, `/ready`, `/admin`, `/docente`, `/estudiante` y los flujos offline antes de promover a producción.

## Siguiente paso

Ejecutar `scripts/publicar_en_github.ps1` desde una terminal PowerShell autorizada y confirmar el enlace de la rama. Después se puede crear un **servicio nuevo y aislado** en Render desde esa rama y ruta de Dockerfile. No cambiar los servicios KAWSAY existentes.
