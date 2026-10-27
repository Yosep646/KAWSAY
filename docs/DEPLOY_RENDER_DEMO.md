# Despliegue demostrativo en Render

Esta versión integra React y FastAPI en un único servicio para disponer de las rutas `/admin`, `/docente`, `/estudiante` y `/api/v1` sobre una misma URL.

**No utilizar con datos reales de estudiantes.** Render Free no asegura persistencia de archivos: SQLite se perderá al reiniciar o reemplazar el contenedor. El programa original sólo admite SQLite, y `JWT_SECRET` debe configurarse como secreto antes de iniciar. No instalar PostgreSQL sin adaptar primero el código y sus migraciones.

## Publicación
1. Publica el contenido descomprimido del proyecto en un repositorio autorizado, **sin `.env`, bases de datos, credenciales ni información de estudiantes**.
2. En Render, elige Blueprint y conecta el repositorio con el archivo `render.yaml`, o crea un Web Service Docker Free con `dockerfilePath=./render.Dockerfile`.
3. Proporciona `JWT_SECRET` aleatorio de al menos 32 caracteres (por ejemplo, `python -c "import secrets; print(secrets.token_hex(32))"`), **en la configuración privada de Render**.
4. La imagen ejecuta migraciones Alembic al iniciar y sirve la web y API en la misma URL HTTPS.
5. Comprueba `/health`, `/ready` y los paneles web, y crea manualmente un administrador con una contraseña única; no se incluyen usuarios demo.
6. Para producción: PostgreSQL u otra base persistente, backup, evaluación de privacidad y pruebas E2E/offline con dispositivo real.

La compilación de Vite en este entorno todavía no ha sido demostrada con npm completo: la configuración es una receta lista para probar, no evidencia de que el despliegue haya tenido éxito.
