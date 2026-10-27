# Verificación KAWSAY AI — 27 de octubre de 2026

## Evidencia obtenida en este entorno
- Python 3.13.5; Node.js 22.16.0; npm 10.9.2.
- `cd backend && pytest -q tests/test_auth.py tests/test_assignments.py`: **26 passed**.
- `cd backend && pytest -q tests/test_sync_reto10.py`: **11 passed**.
- `cd ml && pytest -q tests/test_ml_pipeline.py`: **17 passed**.
- Total de pruebas seleccionadas verificadas: **54 aprobadas**.
- `node --check teacher-web/public/sw.js`: **sin error sintáctico**.
- Suite completa backend: llegó a 51% sin fallos mostrados; **no finalizó** por límite de ejecución, por lo que no se declara aprobada.
- `cd teacher-web && npm ci --offline --ignore-scripts --no-audit --no-fund`: **error ENOTCACHED**, falta `xmlchars-2.2.0.tgz`.
- `npm ci` conectado: no terminó dentro del límite. Node 22.16.0 no satisface los requisitos declarados por dependencias que solicitan >=22.22.2 o >=24.15.0.
- Por falta de `node_modules`, **no se pudo completar `npm run build`, ni Vitest, ni Playwright**.
- **No se ha realizado prueba offline en navegador** (IndexedDB, pérdida de red, reapertura y reintentos). Los 11 tests de sincronización backend no prueban esa experiencia completa.

## Cómo completar pruebas en un entorno funcional
Usar Node.js 24.15.0 o posterior de la rama 24 (o una versión que satisfaga todos los engines), con acceso al registro npm:

```bash
cd teacher-web
npm ci
npm run typecheck
npm run build
npm test
npm run test:integration
npm run test:e2e
```

Validar navegador con HTTPS o localhost y probar: descargar una actividad, responder múltiples preguntas offline, recargar/cerrar y reabrir, reconectar, verificar respuestas idempotentes y progreso en panel docente.

## Estado
Este documento registra verificaciones ejecutadas, **no certifica** funcionamiento offline, compilación React ni integración E2E de tres perfiles. No se modifica el modelo ML experimental ni se asegura entrenamiento con datos reales.
