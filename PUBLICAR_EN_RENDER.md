# KAWSAY AI — publicación en GitHub y Render

## Repositorio oficial de esta entrega

**https://github.com/Yosep646/KAWSAY** (ya creado por el usuario, inicialmente vacío).

## Paso 1. Subir el código al repositorio existente

1. Instala Git en Windows y configúralo con tu cuenta de GitHub.
2. Extrae este ZIP en una carpeta nueva, sin archivos `.git` antiguos.
3. Abre PowerShell dentro de `KAWSAY-AI` y ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\SUBIR_A_KAWSAY.ps1
```

El script comprueba archivos y credenciales a través de Git, rechaza posibles secretos o bases de datos y se detiene si `main` ya contiene commits. No hace `force push`. **No necesitas crear otro repositorio.**

## Paso 2. Publicar en Render

1. Abre https://dashboard.render.com/blueprints e inicia la creación de un Blueprint nuevo.
2. Conecta el repositorio `Yosep646/KAWSAY`, rama `main`.
3. Render detectará `render.yaml` y `render.Dockerfile`.
4. Configura `JWT_SECRET` como secreto nuevo aleatorio, exclusivamente desde Render. No lo incluyas en GitHub.
5. Revisa logs, estado del build y `/health`, `/admin`, `/docente`, `/estudiante` antes de compartir la URL.

**Esta configuración es solo para demostraciones con datos ficticios.** Render Free no conserva los datos SQLite almacenados en su disco temporal y el entrenamiento de ML no está validado con estudiantes reales. Para una instalación escolar real hay que usar almacenamiento externo persistente con copias de seguridad y cumplir controles de protección de datos.

La compilación completa de React, el funcionamiento offline en navegador y el despliegue en Render deben verificarse realmente; no se infieren de las pruebas unitarias.
