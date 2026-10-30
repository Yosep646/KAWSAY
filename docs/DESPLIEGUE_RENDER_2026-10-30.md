# Demostración remota del ZIP actualizado

Rama aislada `codex/render-offline-20261030` en el repositorio de KAWSAY ya conectado a Render. No sustituye `main` ni el servicio anterior.

El entry point `app.deploy:application --factory` sirve la compilación React y la API bajo el mismo origen. `/sw.js` devuelve JavaScript y permite alcance raíz, las rutas de React reciben HTML y las rutas API inexistentes continúan devolviendo 404. Las migraciones se ejecutan al iniciar, antes de uvicorn. El usuario del contenedor no es root.

Se conserva íntegra la lógica de la entrega local `d287599`; la adaptación agrega `render.Dockerfile`, `.dockerignore`, el servidor estático, inicialización DEMO y dos pruebas específicas. Los artefactos binarios experimentales ML y capturas de pruebas se conservan en el ZIP descargable y no se publican en esta rama de despliegue ni en la imagen. No hay modelo aprobado que dependa de ellos.

Variables requeridas: `APP_ENV=production`, `DATABASE_URL=sqlite:////srv/data/kawsay.db`, `JWT_SECRET` aleatorio, `KAWSAY_DEMO_BOOTSTRAP=1` y correos/contraseñas DEMO ADMIN y TEACHER mediante secretos de Render. No se incorporan sus valores a Git. El origen de API se mantiene vacío durante la compilación para usar el mismo origen HTTPS.

Plan Free: instancia única, base SQLite temporal. Reinicios, inactividad y despliegues pueden eliminar los datos. La copia local cifrada del estudiante no permite reconstruir una base remota reiniciada con nuevos identificadores de usuarios y actividades. Esta demostración requiere únicamente datos ficticios y no acredita persistencia institucional. El despliegue persistente requiere otra fase y recursos adecuados.
