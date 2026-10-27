# Auditoría técnica KAWSAY AI

Fecha: 26 de octubre de 2026. Rama: `audit/modernizacion-kawsay`.

## Alcance y evidencia

**Entrega parcial: no se cumplen todavía todos los criterios del piloto.**
Se inventarió recursivamente el código propio, configuración, documentación,
recursos y artefactos. El detalle por ruta, tamaño, hash de texto y análisis
estructural está en [INVENTARIO_ARCHIVOS.md](INVENTARIO_ARCHIVOS.md) y su JSON.
El inventario distingue explícitamente sintaxis, presencia y comprobación
funcional: **no equivale a una revisión semántica individual completa**.
La revisión manual se concentró en los flujos y archivos citados abajo; la
revisión semántica del resto continúa pendiente.

Los paquetes de `.venv/` y `node_modules/` son instalaciones de terceros,
necesarias para las verificaciones locales, excluidas del análisis individual.
No se leyeron archivos `.env`, bases con información educativa ni binarios de
modelos para inventariarlos. El registro y reportes ML sí se inspeccionaron.
No se encontró un repositorio Git previo: se inicializó uno, sin historia anterior
que permita comparar el estado recibido con commits previos.

## Arquitectura encontrada

- `backend/app/core`, `domain` y `modules/<dominio>/{routes,schemas,service,models}`:
  monolito modular FastAPI/SQLAlchemy. Es equivalente a la separación solicitada;
  conservarlo evita mover módulos sin beneficio demostrado.
- `backend/migrations`: Alembic, una revisión inicial SQLite.
- `teacher-web/src`: React, TypeScript, Vite, rutas protegidas, páginas y cliente central.
- `mobile/lib/{app,core,features,shared}`: Flutter, SQLite y cola persistente.
- `ml/`: simulador, características, entrenamiento, registro, inferencia, exportador y reportes.
- `automation/n8n/workflows`: un workflow; dispatcher y outbox en backend.
- `ai/`, `database/`, `infrastructure/`: documentación de componentes, no servicios independientes completos.

SQLite servidor es una decisión explícita (ADR-010), con WAL, claves foráneas,
busy timeout y `BEGIN IMMEDIATE`. Se verifican concurrencia e idempotencia en
pruebas, no capacidad de producción. PostgreSQL exige adaptación de configuración,
migraciones y triggers: no basta con cambiar la URL. Evaluarlo con carga real
antes de necesitar múltiples escritores/réplicas.

## Hallazgos por ruta

| Ruta / función | Problema y gravedad | Solución / estado | Evidencia |
|---|---|---|---|
| `backend/alembic.ini`, `backend/tests/conftest.py`, `test_health.py` / migraciones | Alta: rutas relativas al cwd rompían pruebas desde raíz | Corregido con `%(here)s` y ruta absoluta a configuración | Inicial: 130 errores desde raíz; regresión posterior desde raíz aprobada |
| `backend/app/modules/forecast/service.py` / inferencia | Alta: enviaba `wrong=0` aun con errores reales; divergencia entrenamiento-inferencia | Corregido: `wrong_attempts` real | Prueba de integración con un error y posterior acierto |
| Mismo servicio | Alta: fallo posterior a cargar el modelo podía romper la analítica | Fallback explícito sin probabilidad fabricada; tiempo `inference_ms` | Prueba con predictor que lanza excepción; HTTP 200 con `available=false` |
| `ml/train.py` / calibración | Alta: CV interna de calibración con `cv=3` mezclaba estudiantes | Corregido: folds agrupados también en calibración anidada | Prueba de disyunción en ambos niveles; nuevo entrenamiento ejecutado |
| `ml/features.py` / dataset | Alta: aceptaba NaN, valores fuera de rango y columnas adicionales | Validación previa: esquema limitado, grados 1–6, resultados cerrados, conteos y scores finitos | Pruebas con NaN, scores inválidos, booleanos y columna personal |
| `ml/train.py`, `ml/requirements.txt` | Media: librerías ML con mínimos abiertos, sin runtime en reportes | Versiones directas fijadas a las ejecutadas; runtime y protocolo v2 registrados | Entrenamiento, `pip check` y pruebas ML |
| `ml/make_model_card.py` | Media: podía atribuir robustez de otro protocolo y afirmar solapamiento de IC no calculado | No reutiliza robustez incompatible; aclara ausencia de comparación pareada | Ficha regenerada del nuevo candidato |
| `ml/common.py`, `registry.py`, `train.py`, `export_real.py`, `robustness.py`, `make_model_card.py` | Media: codificación por defecto de Windows rompía la generación de ficha | Escritura UTF-8, lector de reportes históricos UTF-8/cp1252 | Se observó `UnicodeEncodeError`; ficha regenerada correctamente tras corrección |
| `teacher-web/src/services/api.ts` | Alta: fallo temporal del refresh eliminaba sesión; sin timeout ni cancelación | Conserva sesión ante 503/red, timeout de 15 s y `AbortSignal`; clasifica JSON inválido | Pruebas de refresh temporal, timeout, HTML inesperado y cancelación |
| `teacher-web/src/hooks/useAsync.ts` | Media: una respuesta antigua podía sobrescribir el aula seleccionada | Generaciones de petición e invalidación al desmontar/cambiar dependencias | Prueba con promesa antigua que termina después de la nueva |
| `teacher-web/src/pages/Dashboard.tsx`, `types/api.ts` | Media: error en alertas aparecía junto a mensaje de ausencia de alertas; faltaba versión ML visible | Estados de error diferenciados, actualización manual real y versión del modelo | TypeScript, Vitest, build y E2E |
| `scripts/browser_e2e.py` | Media: integración HTTP web se excluía de unitarias y no se ejecutaba en E2E | Ejecuta el test real en el servidor temporal antes de Playwright | 1 integración HTTP y 5 E2E aprobados |
| `mobile/lib/app/session.dart`, `core/data/repository.dart` | Crítica: logout conservaba perfil restaurable y almacenamiento no delimitaba propietario | Perfil eliminado al salir, restauración requiere token; vinculación persistente a un estudiante; bloqueo con trabajo pendiente | Revisión estática; prueba de aislamiento añadida **sin ejecutar** |
| `mobile/lib/core/sync/sync_manager.dart` | Alta: resultados incompletos/malformados dejaban eventos SYNCING; estado idle ocultaba error | Validación completa de ACK por UUID, actualización transaccional, reintento de no confirmados, conflictos separados, cursor validado | Revisión estática; prueba de respuesta incompleta añadida **sin ejecutar** |
| Mismo módulo y `features/home/home_screen.dart` | Alta: timers podían continuar tras salir y se mostraba «Todo sincronizado» con errores | Parada coordinada, reinicio sin listeners duplicados y mensajes basados en cola | Revisión estática; requiere prueba Flutter |
| `mobile/lib/core/api/api_client.dart` | Alta: error temporal renovando token se trataba como sesión expirada | Renovación compartida, red/HTTP/JSON diferenciados y timeout de logout | Revisión estática; pendiente SDK |
| `mobile/lib/core/database/app_database.dart` | Alta: SQLite sin cifrado; migraciones futuras no definidas | Pendiente SQLCipher o mecanismo equivalente con claves y migraciones verificadas | `sqflite`, schemaVersion=1; no implementación de cifrado encontrada en este módulo |
| `mobile/lib/features/assignments/activity_screen.dart` | Alta: se persisten respuestas enviadas, no borrador del campo/pistas; riesgo de doble toque y setState tras desmontar | Pendiente persistencia de borrador y revisión de ciclo de vida | Lectura del flujo `_answer`, `_help`, `_load`; solo intentos en SQLite |
| `mobile/` | Bloqueante: faltan carpetas de plataforma Android y validación en dispositivo | Flutter y SDK Android instalados; pendientes avisos analyze, plataforma, build y dispositivo | `flutter test`: 11 aprobadas con API falsa; `flutter analyze`: 8 avisos; `flutter doctor -v` reconoce Android; `adb devices` sin dispositivos |
| `mobile/lib/app/session.dart` | Alta: autorización offline basada en sesión previa, sin desbloqueo local ni política de expiración propia | Pendiente mecanismo local autorizado, compartición segura de equipos y revocación al reconectar | Lectura de restore/login; no validación en dispositivo |
| `backend/app/modules/sync/service.py`, `learning/models.py` | Media: eventos son append-only, pero resolución pedagógica de respuestas concurrentes entre dispositivos requiere política explícita | No se sobrescribe trabajo; pendiente validar caso real entre dispositivos y revisión docente | Clave única incluye dispositivo; pruebas existentes de repetición/concurrencia del mismo evento |
| `backend/app/modules/sync/service.py` / idempotencia | Alta: reutilizar UUID con una respuesta distinta se confirmaba como DUPLICATE, pudiendo ocultar trabajo no guardado | Se compara el intento persistido; contenido distinto produce `REJECTED`/`event_id_conflict`, que el cliente conserva como conflicto | Prueba de respuesta modificada y 14 pruebas de sync/concurrencia; no sustituye prueba en dispositivo |
| `ml/registry.py` | Alta para producción: aprobación real exige revisor y datos REAL, pero no impone expediente completo de aceptación | Pendiente gates de promoción vinculados a evaluación educativa y revisión documentada | Lectura de `approve`; sintético sigue bloqueado |
| `ml/train.py` / entrada real | Alta: un JSONL suministrado directamente evitaba los mínimos impuestos por el exportador | Corregido: valida esquema y exige los mismos mínimos antes de entrenar; autorización y procedencia siguen siendo requisitos externos | Prueba con archivo pequeño rechazada; 17 pruebas ML aprobadas |
| `ml/export_real.py` | Alta: grado numérico sin nivel permitía mezclar primaria y secundaria; la API de exportación aceptaba sal corta | Corregido: filtra primaria 1–6 y valida sal en la función; secundaria requiere otro esquema | Prueba SQLite con estudiantes de ambos niveles y rechazo de sal corta; 15 pruebas ML aprobadas |
| `ml/predict.py` | Media: deserialización joblib presupone artefactos confiables; sin verificación criptográfica del artefacto | Preservado; pendiente integridad y carga cacheada con invalidación por versión | Lectura de `load`; acceso solo al repositorio local de modelos |
| `ml/predict.py` / selección de modelo | Alta: un registro inconsistente podía señalar como aprobado un modelo sintético | Corregido: inferencia normal requiere `APPROVED` y `data_kind=REAL`; la procedencia declarada no demuestra autenticidad ni validación educativa | Prueba de registro sintético marcado aprobado; regresión backend/ML: 148 aprobadas |
| `teacher-web/` | Media: panel no es PWA offline, no hay módulo completo de reportes/exportación ni cursos independiente | Pendientes de alcance; no presentar el panel como solución offline integral | Estructura de páginas y navegación; sin service worker inventariado |
| `automation/n8n/workflows/01_support_flag_notify.json` | Alta: preparaba un mensaje sin enviarlo y confirmaba entrega; rawBody depende de n8n | Alertas sin canal responden 503, otros eventos válidos se descartan; pendiente ejecución HTTP y entrega autorizada | Importación exitosa en n8n 2.44.7 aislado; pruebas backend usan receptor simulado |
| `backend/app/modules/automation/dispatch.py` / verificación HMAC | Media: timestamp no numérico provocaba excepción y `NaN` podía eludir la comparación de antigüedad | Rechaza entradas malformadas y no finitas antes de verificar la firma | Pruebas para `nan`, infinitos, texto y vacío; regresión backend/ML aprobada |
| `backend/app/modules/automation/routes.py` / reintento | Media: el reencolado administrativo no registraba quién lo solicitó | Añadido registro de auditoría en la misma transacción del cambio a PENDING | Prueba de rol, estado y registro; 155 pruebas backend/ML aprobadas |
| `docker-compose.yml` | Media: falta comprobar ejecución integrada de backend/web/dispatcher | Motor Docker arrancado; imágenes backend y web compiladas; backend aislado responde a health; ejecución integrada pendiente | `docker build` correcto para backend y web; `/health` HTTP 200 en contenedor; no se probó compose ni n8n |
| `teacher-web/.dockerignore` | Media: el contexto Docker incluía `node_modules`, resultados y potenciales archivos `.env` | Añadido `.dockerignore` para excluir dependencias, generados y secretos | Build de web correcto; primera transferencia reportó 126,83 MB antes de la exclusión |
| `backend/requirements.txt` y entorno Python | Baja: TestClient advierte transición de httpx a httpx2 | Pendiente migración compatible del transporte de pruebas | Pytest aprueba con una advertencia de Starlette; pip-audit sin vulnerabilidades conocidas |
| `.gitignore`, cachés y directorios E2E | Media: no había historial; no había recuperación Git para archivos recibidos | Ignore ampliado, datos y artefactos preservados, sin borrados | `git check-ignore` confirma exclusión de secretos, DB y dependencias |

## Estado funcional

**Verificado en esta máquina:** backend HTTP iniciado por E2E; autenticación,
roles/propiedad, planificación y publicación multigrado, persistencia de intentos,
sync idempotente en servidor, progreso/alertas por reglas, frontend docente
conectado y diseño sin desbordamiento en los viewports probados, entrenamiento
sintético, inferencia experimental en pruebas y fallback.

**Parcial:** aplicación Flutter y correcciones móviles (solo inspección),
currículo de demostración, recomendaciones por reglas, ML experimental,
outbox de automatización con receptor simulado, documentación OpenAPI con varias
respuestas tipadas como diccionarios en vez de esquemas de salida completos.

**No demostrado o no implementado completamente:** compilación Android, diez
escenarios offline en dispositivo, cifrado SQLite, autenticación local controlada,
sincronización multidispositivo funcional, reportes/exportaciones, aprendizaje
multimedia descargable, conformidad WCAG 2.2 AA completa, notificación n8n real,
modelos autorizados con datos reales y despliegue Docker.

## Dependencias y duplicados

`npm audit --json`: 0 vulnerabilidades conocidas. `pip-audit -r
backend/requirements.txt`: sin vulnerabilidades conocidas. `pip check`: sin
requisitos rotos. Esto no demuestra que todas las versiones sean las últimas ni
ausencia de vulnerabilidades desconocidas. La revisión de obsolescencia completa
y el bloqueo transitivo ML/Flutter quedan pendientes.

No se detectaron duplicados binariamente idénticos entre los archivos de texto
no vacíos incluidos en el inventario inicial. Los `__init__.py` vacíos son
marcadores de paquete, no candidatos automáticos a eliminación. Similitud lógica
o versiones semánticamente redundantes no se certificaron.

## Verificaciones y seguimiento

Comandos y resultados: [VERIFICACION_2026-10-26.md](VERIFICACION_2026-10-26.md).
Contrato: [INTEGRACION_API.md](INTEGRACION_API.md), [openapi.json](openapi.json).
Modelo: [ml-model-card.md](ml-model-card.md).
La revisión semántica completa y las condiciones pendientes del piloto siguen abiertas.
