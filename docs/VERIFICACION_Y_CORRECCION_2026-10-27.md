# KAWSAY AI — Verificación y corrección (27/10/2026)

## Cambios realizados
- `teacher-web/src/services/offlineTasks.ts`: guardar resúmenes de actividades ya no elimina preguntas descargadas previamente; conserva el contenido completo para trabajo sin conexión cuando llegan listas parciales del servidor.
- Los archivos de terceros `node_modules` no se incluyen en el paquete de entrega para impedir reutilizar una instalación incompleta.

## Pruebas ejecutadas
- `python -m pytest -q backend/tests/test_auth.py backend/tests/test_assignments.py backend/tests/test_sync_reto10.py ml/tests`: **54 passed**.
- `python -m compileall -q backend/app ml`: **correcto**.
- `node --check teacher-web/public/sw.js`: **correcto**.
- `npm run preflight`: **falla** en este entorno porque Node es 22.16.0, y el proyecto requiere >=24.15.0.
- `npm run build`: **no completada**, faltan dependencias de TypeScript/Vite/Vitest en node_modules local.
- La resolución DNS de registry.npmjs.org falla en este contenedor, así que no es posible completar aquí `npm ci`.

## Limitaciones pendientes
- Las 54 pruebas son pruebas Python seleccionadas, no incluyen prueba real del navegador.
- Falta validar React usando Node 24.15+ y npm accesible.
- Falta ejecutar casos offline reales con navegador: descargado de actividades, respuesta a varias preguntas, recarga sin red, retorno de red y ausencia de duplicados.
- El login offline después de cerrar la sesión no está soportado: no describir el producto como completamente offline.

## Ejecutar en Windows actualizado
En `teacher-web`:
```
node -v
npm ci --no-audit --no-fund
npm run preflight
npm run typecheck
npm run build
npm test
npm run test:integration
npm run test:e2e
```
Si `node -v` aún muestra 22, cierra la terminal y abre otra; comprueba `where.exe node`.
