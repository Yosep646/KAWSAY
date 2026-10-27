# 00 · Auditoría del repositorio (estado real al cierre)

Clasificación: **IMPLEMENTED** (código + pruebas ejecutadas) · **PARTIAL** · **UNVERIFIED** (escrito, no ejecutado) · **PLANNED** · **BLOCKED**.
Regla: nada se marca IMPLEMENTED sin una verificación ejecutada. Autor: Yosep.

## Verificaciones ejecutadas en el cierre
| Verificación | Resultado |
|---|---|
| `pytest` backend (SQLite) | **130 passed** |
| `pytest` ML | **9 passed** |
| `vitest` panel docente + `tsc` + `vite build` | **13 passed**, tipos y build limpios |
| Integración real del panel contra el backend (login, aulas, alertas con evidencia, refresco de token) | passed |
| E2E en Chromium real (Windows, 2026-10-26): sesión, evidencia/progreso, intervención/filtros, idiomas y diseño adaptable | **5 passed** (`npm run test:e2e` en `teacher-web/`); SQLite temporal + backend real, sin mocks |
| `ruff`, `mypy` | limpios |
| `bandit` (severidad media/alta) | sin hallazgos |
| `pip-audit` / `npm audit` | sin vulnerabilidades conocidas (se actualizaron FastAPI/Starlette/PyJWT/Vite/Vitest/React Router) |
| Migración 0001 sube → baja → sube en SQLite; datos base y triggers presentes; `integrity_check` ok | ok |
| **Copia limpia del proyecto**: `dev.py setup` (22 s) + `dev.py demo` → 10/10 pasos, alerta con evidencia generada | ok |
| Concurrencia: 24 hilos (login/escritura), refresh simultáneo, 6 envíos simultáneos del mismo lote, llamada lenta de IA | sin errores, sin duplicados, sin bloqueos |

## Estado por componente
| Componente | Estado |
|---|---|
| Backend: auth, RBAC/propiedad, escuelas, aulas multigrado, estudiantes (código+PIN) | IMPLEMENTED |
| Planificación curricular versionada (UGEL/año/periodos/unidades/temas; BORRADOR→ACTIVA; 1 activa por plan) | IMPLEMENTED |
| Asignaciones multigrado, variantes por grado, revisión/aprobación docente, publicación inmutable | IMPLEMENTED |
| Sync push/pull idempotente, intentos append-only, corrección en servidor | IMPLEMENTED (contrato probado con cliente simulado) |
| Progreso por competencia, detector R-SUP-001, alertas con evidencia, intervenciones, fortalezas, motivación | IMPLEMENTED (reglas) |
| "Quiero aprender" (API) y tutor guiado | IMPLEMENTED |
| AI Gateway + validadores (salida y curricular) | IMPLEMENTED con proveedor **falso solo en pruebas**; adaptador Anthropic UNVERIFIED en vivo |
| Idiomas y traducciones humanas verificadas | IMPLEMENTED; elección declarada desde app o panel docente; sin variantes ni traducciones cargadas (no se inventan) |
| Seguridad (ver `14-security.md`) | IMPLEMENTED y probada; riesgos residuales listados |
| Auditoría de accesos, eventos de dominio (outbox), webhooks firmados | IMPLEMENTED |
| Respaldos y verificación de la base SQLite (`app.cli backup/check-db`) | IMPLEMENTED |
| Panel docente (React/TS) | IMPLEMENTED, incluida gestión de estudiantes e idiomas; 5 E2E en Chromium real (no cubren todas las pantallas) |
| ML: pipeline, validación cruzada, calibración, IC, robustez, registro, inferencia, exportador | IMPLEMENTED |
| Modelo entrenado | EXPERIMENTAL (sintético, no aprobado, sin ventaja demostrada sobre una heurística simple) |
| Pronóstico ML en backend | IMPLEMENTED, **desactivado sin modelo aprobado** |
| Tooling VS Code (`dev.py`, `.vscode`) | IMPLEMENTED; copia limpia probada en Linux y `setup` + suites probados en Windows |
| **App Flutter del estudiante** | **UNVERIFIED**: 22 archivos Dart nunca compilados |
| **Funcionamiento offline real en un celular** | **NO DEMOSTRADO** |
| n8n (workflow 01) | UNVERIFIED (JSON no importado en n8n real) |
| Docker Compose / CI de GitHub | UNVERIFIED (sin Docker; CI no ejecutado en GitHub) |

## NO existe / pendiente
- Compilar y probar la app Flutter; SQLCipher en el móvil; Learning Packs con imágenes/audio; prueba offline manual con modo avión.
- Ampliar E2E de navegador a planificación/publicación y administración, otros navegadores y build servido en producción; validación de usabilidad con docentes y estudiantes; pruebas de carga.
- Datos reales: currículo oficial, estudiantes, intervenciones; por eso no hay modelo ML aprobado.
- Proveedor de IA real evaluado con docentes; n8n real; revisión legal de datos de menores; pruebas de penetración externas.
- Modo ADAPTIVE_POOL (rechazado con 422), reportes exportables, notificaciones push.

## Riesgos y deuda técnica
- SQLite: un solo escritor y sin cifrado en reposo (ver ADR-010 y `14-security.md`).
- Rate limit y circuit breaker en memoria (un solo proceso).
- Refresh token del panel en `sessionStorage`.
- `device_id` de sync no es entidad (sin revocación por dispositivo).
- Defectos hallados por las pruebas durante el desarrollo y corregidos: FK sin nombre en migración, fuga de respuesta de una letra en el tutor,
  validador de complejidad que diluía oraciones largas, desfase de reloj, `SMALLINT PRIMARY KEY` sin autoincremento en SQLite,
  respaldos que se pisaban en el mismo segundo, y varias dependencias con vulnerabilidades conocidas.
- Si el disco montado es lento, instalar `node_modules` en un directorio local.

## Continuación verificada — 2026-10-26
- `python scripts/dev.py setup` y `python scripts/dev.py test`: 130 backend + 9 ML + 13 panel, sin fallos.
- Añadido Playwright 1.64.1 con Chromium y ejecutor de servidores aislados (`scripts/browser_e2e.py`): migración, carga DEMO por API, navegador y cierre de procesos con eliminación de SQLite temporal. Puertos exclusivos 18000/15173; no utiliza la base de desarrollo. Ver `16-testing.md`.
- E2E: 3 passed. Tipos del panel y del E2E, build, ruff/mypy del ejecutor: limpios.
- Auditoría Python detectó PYSEC-2026-1845 en pytest 8.3.4 (directorios temporales en Unix); actualizado a **9.0.3** y repetidas las suites backend/ML/panel. `pip-audit` y `npm audit`: sin vulnerabilidades conocidas tras el cambio.
- Permanece un aviso de deprecación de Starlette sobre TestClient/httpx; las pruebas pasan.
- Flutter/Dart no disponibles en PATH. Docker CLI instalado, pero `docker version` no conecta al motor de Docker Desktop. App móvil y despliegue Docker siguen sin verificar.

### Mejora visual del panel — 2026-10-26
- Navegación lateral en escritorio y navegación superior adaptable en móvil; sección activa, identidad docente y enlace para saltar al contenido por teclado.
- Acceso con identidad visual e ilustración SVG local, mostrar/ocultar contraseña, formularios accesibles. Sin fuentes, imágenes ni dependencias externas nuevas.
- Dashboard con resumen por aula, distribución por grado, alertas con evidencia, fortalezas y ML opcional. Datos y cantidades proceden de la API; errores de fortalezas y pronóstico se muestran explícitamente.
- Estilos compartidos de formularios, tablas, tarjetas y estados de carga; tabla de evidencia desplazable dentro de su contenedor, modo oscuro según el sistema y respeto a movimiento reducido.
- Corregida la etiqueta visual de alertas RESOLVED/DISMISSED (antes se mostraban como «En seguimiento»).
- Verificación: 13 pruebas unitarias y 5 E2E passed, tipos de aplicación/E2E y build correctos. Capturas revisadas en escritorio y móvil emulado, incluidos tema oscuro y acceso. No se repitieron las suites backend/ML en esta tarea de interfaz.
- En la verificación apareció un bloqueo transitorio al eliminar SQLite en Windows tras finalizar Chromium; el ejecutor ahora reintenta la limpieza durante hasta 5 segundos sin ocultar fallos persistentes. Comando E2E completo repetido y finalizado correctamente; ruff/mypy del ejecutor limpios.
- Panel local en `http://127.0.0.1:5173` comprobado con HTTP 200 y sirviendo los estilos nuevos.
