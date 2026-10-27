# KAWSAY AI — Compilación y conectividad (27/10/2026)

## Entorno
- Node.js 22.16.0, npm 10.9.2, Python 3.13.5.
- Frontend en `teacher-web`; backend en `backend`.

## Pruebas realmente ejecutadas
- `python -m pytest backend/tests/test_auth.py backend/tests/test_assignments.py backend/tests/test_sync_reto10.py -q --disable-warnings`: **37 passed**.
- `python scripts/verify_web_role_wiring.py`: comprobaciones estáticas de las tres rutas de acceso por rol, cliente API compartido y autenticación. Esta comprobación **no** prueba el navegador ni el flujo de extremo a extremo.
- La suite total `python -m pytest backend/tests -q -x --disable-warnings` avanzó al menos hasta el 51 % y terminó por límite de ejecución. No se informa como aprobada.

## Compilación web — bloqueada
- `npm ci --ignore-scripts --no-audit --no-fund --prefer-offline` no terminó dentro de 90 s.
- Dependencias como `jsdom@30.1.3` y `undici@8.12.3` requieren Node más reciente que 22.16.0; `vite`/`tsc` no quedaron instalados completamente.
- **No se ha realizado con éxito** `npm run build`, pruebas Vitest ni pruebas reales en navegador. No afirmar lo contrario.

## Para terminar la validación en un entorno con red y Node compatible
```bash
cd teacher-web
node --version
npm ci
npm run typecheck
npm run build
npm test
npm run test:integration
```
Iniciar backend y ejecutar pruebas Playwright y flujo de docente que publica actividad, estudiante que la recibe/resuelve y docente que visualiza resultados. Verificar 3 roles con cuentas de prueba aisladas. No usar datos personales reales.

## Estado de la conexión
- La web utiliza cliente común `teacher-web/src/services/api.ts` con prefijo `/api/v1`.
- Las tres rutas están protegidas en `teacher-web/src/app/App.tsx`.
- **Autenticación, actividades y sincronización:** 37 pruebas del backend aprobaron.
- **Conexión real de tres interfaces en navegador:** pendiente hasta que el frontend compile, se inicie y se pruebe con el backend.
