# React y offline — resultados verificables (27/10/2026)

## Cambios realizados
- Actualizada la imagen de compilación Docker de `node:22-alpine` a `node:24-alpine` para satisfacer los requisitos de las dependencias Vite/jsdom actuales.
- Añadido `teacher-web/nginx.conf`, que era referenciado por el Dockerfile pero no existía; incluye fallback a `index.html` para rutas React.
- Cola IndexedDB versionada a v2: permite varios eventos pendientes por actividad, con identificador individual y migración de registros previos.
- El estudiante puede continuar respondiendo otras preguntas mientras haya eventos no sincronizados, y ve un indicador de pendientes.
- Reintento controlado, sin bucle inmediato infinito ante fallo de red, y eliminación individual solo tras ACK/DUPLICATE y lectura de estado servidor.

## Resultados ejecutados
- `python -m pytest -q backend/tests/test_sync_reto10.py`: **11 passed**.
- 5 verificaciones estáticas de elementos clave de la cola: **5 correctas**.
- `npm run build`: **falló** debido a módulos y archivos de tipos faltantes en `node_modules` (`vite/client`, `vitest/globals`, `@testing-library/jest-dom`).
- `npm ci --ignore-scripts --no-audit --no-fund --prefer-offline`: **no finalizó** dentro del tiempo límite. Entorno: Node 22.16.0, incompatible con requisitos de algunas dependencias y sin descarga completa del registro npm.

## Pendientes (no deben describirse como verificados)
- Compilación final con `node:24`, `npm ci`, `npm run build` y `npm test` en un entorno con acceso al registro npm.
- Pruebas reales de IndexedDB en navegador: migración v1→v2, 10 respuestas offline, recuperación tras cierre de pestaña y sincronización tras volver Internet.
- Pruebas E2E de los tres roles, más Flutter y entrenamiento con dataset real autorizado.

## Cómo verificar en un equipo con Internet
```bash
cd teacher-web
node --version  # versión 24.x
npm ci
npm run typecheck
npm run build
npm test
npm run test:e2e
```
No subir este ZIP a producción sin completar esas verificaciones.
