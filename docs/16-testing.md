# 16 · Estrategia de pruebas

Suites backend, ML y unitarias del panel: `python scripts/dev.py test` (o por partes). E2E de navegador: comando separado abajo. Cada prueba del backend usa **su propia copia** de la base SQLite migrada.

| Suite | Cantidad | Qué cubre |
|---|---|---|
| `backend/tests` | 130 | auth y sesiones, RBAC/IDOR, multigrado, planificación versionada, asignaciones y revisión docente, sync idempotente, Reto 10 (alerta con evidencia), IA con proveedor falso (caída, timeout, salida inválida, desvío curricular), tutor, idiomas, outbox/webhooks, auditoría, seguridad, concurrencia SQLite, pronóstico ML, vectores compartidos Python↔Dart |
| `ml/tests` | 9 | determinismo, partición sin fuga por estudiante, etiqueta solo con el futuro, validación cruzada agrupada, IC, registro (no aprueba sintéticos), exportador seudonimizado con guarda, inferencia solo con modelo aprobado |
| `teacher-web` (vitest) | 13 + 1 integración | cliente API (refresco de token), tarjeta de alerta con evidencia, control de acceso, editor de preguntas, estudiantes e idiomas; integración real contra el backend |
| `teacher-web/e2e` (Playwright) | **5 ejecutadas, passed** | Chromium real contra backend y SQLite temporal: login, evidencia/progreso, refresh tras recarga, logout, intervención persistida/filtros, preferencias de idioma y diseño adaptable en escritorio/móvil |
| `mobile/test` (Dart) | 2 archivos | **escritos, NO ejecutados** (sin SDK de Flutter) |

Escáneres: `ruff`, `mypy`, `bandit`, `pip-audit`, `npm audit`, `tsc --noEmit`.
Pruebas de carga: **no existen**. La prueba offline en un celular es manual (ver `mobile/README.md`).
Datos: los proveedores de IA falsos viven solo en `backend/tests/fakes.py`; ningún dato DEMO se presenta como real.

## E2E en navegador real — verificado en Windows (2026-10-26)

Requisitos: ejecutar `python scripts/dev.py setup` desde la raíz, Node compatible con Vite y Chromium de Playwright.
Desde `teacher-web/`:

```bash
npm ci
npx playwright install chromium
npm run test:e2e
```

En Linux, `npx playwright install --with-deps chromium` instala también bibliotecas del sistema (puede requerir permisos).
El comando comprueba tipos con `tsconfig.e2e.json`; `e2e/run.cjs` selecciona el Python de `.venv` de Windows o Unix y ejecuta `scripts/browser_e2e.py`.
Ese ejecutor:
1. Rechaza puertos ocupados (**18000** backend, **15173** panel) para evitar reutilizar un servidor ajeno.
2. Crea una SQLite temporal `.kawsay-e2e-*` en la raíz, migra y carga el flujo DEMO por API (`demo_e2e.py`). Genera un JWT_SECRET efímero y desactiva IA, ML experimental y webhooks.
3. Sirve el panel con Vite y ejecuta Chromium contra el backend real, sin interceptar ni simular peticiones. Un solo worker; cada prueba usa un contexto de navegador nuevo y la misma base DEMO de la ejecución.
4. Propaga el fallo de las pruebas, detiene ambos servidores (incluidos hijos en Windows) y elimina la base temporal al finalizar normalmente o ante fallos capturados. No modifica la SQLite de desarrollo.

Escenarios comprobados:
- Ruta protegida sin sesión y credenciales incorrectas; login correcto; evidencia de Juan (4/5, 6 pistas, cinco filas de ejercicios), progreso con cinco ejercicios; ML no disponible sin modelo aprobado; refresh real al recargar; restricción de la sección de administración para docente; logout y borrado de refresh local.
- Registro de intervención por formulario (201), consulta autenticada de su persistencia vía API, resolución de la alerta y filtros, estado recuperado tras recargar.
- Preferencias de lengua materna/preferida declaradas por el docente, guardadas y recuperadas tras recargar. No se generan traducciones.
- Dos escenarios visuales (1440×1000 y 390×844): acceso con mostrar/ocultar contraseña, navegación y enlace activo, dashboard y tabla de evidencia sin desbordamiento horizontal del documento, sin errores JavaScript. Capturas de acceso/dashboard/alertas; modo oscuro y movimiento reducido en móvil (emulados en Chromium, no dispositivo físico).

Los escenarios visuales guardan capturas aunque pasen; en fallos también se conserva el trace en `teacher-web/test-results/` (ignorado por Git). Solo contienen datos DEMO y sesiones efímeras de esta ejecución. Las capturas se revisan manualmente, sin comparación automática píxel a píxel.
Se pueden abrir con `npx playwright show-trace <ruta-al-trace.zip>`.

**Límites:** verificado con Chromium headless en Windows y Vite de desarrollo. No cubre todavía planificación/publicación por navegador, administración completa, Firefox/WebKit, nginx/build desplegado, CI real ni usabilidad con docentes. No verifica Flutter ni funcionamiento offline en un celular; la carga inicial simula al cliente móvil.

Dependencias: Playwright fijado en 1.64.1. pytest actualizado de 8.3.4 a 9.0.3 por PYSEC-2026-1845; backend (130), ML (9) y panel (13) pasaron tras la actualización. `pip-audit` y `npm audit` sin vulnerabilidades conocidas. El backend emite un aviso de deprecación de Starlette sobre TestClient/httpx.
