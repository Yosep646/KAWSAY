# Publicar una versión separada en GitHub y Render

La cuenta de Render ya tiene servicios anteriores de KAWSAY AI conectados al repositorio `alcides18huerto-svg/-KAWSAY-AI`. La cuenta GitHub autenticada en ChatGPT es `Yosep646` y tiene acceso de escritura reportado al repositorio, pero esta entrega **no reemplaza main ni las URL anteriores**.

## GitHub

Desde PowerShell en Windows, con una sesión GitHub válida, ejecuta en esta carpeta:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publicar_en_github.ps1
```

Crea una rama separada `deploy/kawsay-demo-20261027` y coloca estos archivos bajo `releases/kawsay-demo-20261027/`. No modifica otras ramas ni otras rutas.

## Render demo

Después de que el push termine, crea un **nuevo** servicio Docker Free, con:

- Repositorio: `https://github.com/alcides18huerto-svg/-KAWSAY-AI.git`
- Rama: `deploy/kawsay-demo-20261027`
- Docker context: `releases/kawsay-demo-20261027`
- Dockerfile: `releases/kawsay-demo-20261027/render.Dockerfile`
- Health check: `/health`
- JWT_SECRET: secreto privado aleatorio de 32+ caracteres.
- APP_ENV: production
- DATABASE_URL: sqlite:////srv/data/kawsay.db
- AI_PROVIDER: disabled

**Atención:** demo con datos ficticios únicamente. SQLite es efímero en Render Free; no subir alumnos reales. Esta receta no demuestra el build hasta que el servicio haya compilado y arrancado de verdad.

Para producción habría que añadir compatibilidad PostgreSQL y migrar todos los flujos, mantener una base persistente, configurar backups y realizar una evaluación de seguridad/privacidad.
