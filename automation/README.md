# Automatización (n8n) — backend operativo; integración SMTP requiere configuración

**Arquitectura:** el backend guarda cada evento de dominio en `domain_events` (outbox transaccional) y el worker
`python -m app.workers.dispatcher` (o `POST /api/v1/automation/dispatch`, solo admin) los entrega por webhook firmado.
**Si n8n cae, KAWSAY sigue funcionando**: los eventos quedan `PENDING` con reintentos exponenciales (máx. 8, luego `FAILED`).
La lógica crítica (auth, RBAC, sync, progreso, alertas) NO está en n8n.

Eventos emitidos (solo ids y conteos, sin nombres): `student.support_flag.created`, `assignment.published`,
`teacher.intervention.created`, `sync.completed`.

## Firma
Cabeceras: `X-Kawsay-Event-Id`, `X-Kawsay-Timestamp`, `X-Kawsay-Signature = sha256=HMAC(secret, "<ts>.<cuerpo crudo>")`.
Probado en `backend/tests/test_automation_languages_tutor.py` (firma válida, manipulada, vieja, secreto erróneo).

## Workflow incluido
`workflows/01_support_flag_notify.json`: verifica la firma, filtra la alerta nueva y prepara un aviso sin PII.
El workflow se importó en n8n 2.44.7 en un contenedor aislado; su ejecución HTTP aún no se ha verificado. Faltan el nodo de envío (correo/WhatsApp) con credenciales y `KAWSAY_WEBHOOK_SECRET`. Una alerta válida responde 503 mientras no haya envío, por lo que el backend la reintenta y eventualmente la marca FAILED; no indica entrega falsa.
Los eventos firmados de otros tipos reciben 200 y se descartan en este workflow; no se procesan ni notifican. No usar este endpoint como destinatario de eventos que deban procesarse hasta implementar sus flujos.
Workflows 2 (resumen semanal) y 3 (Learning Pack publicado): PLANNED.

## Configuración
`.env`: `AUTOMATION_WEBHOOK_URL` y `AUTOMATION_WEBHOOK_SECRET` (≥ 16 caracteres, igual que en n8n). Sin ellas el despachador está desactivado.

Tras corregir la causa de un fallo, un administrador puede devolver un evento `FAILED` a la cola mediante `POST /api/v1/automation/events/{id}/retry`. Se conserva el ID para permitir deduplicación en el receptor. El despacho es al menos una vez: el receptor debe deduplicar por `event_id` antes de enviar notificaciones, porque un fallo tras el envío puede causar un reintento.


## Tutor IA y automatización automática (31/10/2026)

**Lo que hace la aplicación sin n8n:**
1. Alumno: abre **Tutor IA** o una actividad y solicita una pista.
2. Backend: genera una pista mediante Ollama/Anthropic solo si el modelo está configurado y devuelve salida segura; de lo contrario, usa una pista del docente o reglas.
3. Tras dos niveles de ayuda, crea `tutor.help.requested` **una vez por ejercicio** en la base interna.
4. El profesor recibe el aviso en **Alertas educativas** (`GET /api/v1/tutor/help-requests`), con control de permisos por aula. React consulta los nuevos avisos cada 30 s mientras la pestaña está abierta.

**Lo que añade n8n (opcional):**
El workflow `workflows/02_tutor_ia_alertas_educativas.json` valida HMAC del cuerpo crudo, acepta `tutor.help.requested` y `student.support_flag.created` y envía un aviso genérico por **SMTP** al correo institucional configurado. No envía nombres, DNI, respuestas, ni IDs de alumnos. Los otros tipos de evento se reconocen como *ignored*; no son notificaciones.

### Activarlo en una instancia n8n bajo control de la institución

1. Importar `02_tutor_ia_alertas_educativas.json` en n8n.
2. Configurar una **credencial SMTP** en el nodo «Enviar aviso por SMTP» y una cuenta institucional que pueda enviar correos.
3. En el entorno **privado** de n8n establecer:
   - `KAWSAY_WEBHOOK_SECRET`: secreto HMAC aleatorio (mín. 16 caracteres), **idéntico** al del backend.
   - `KAWSAY_NOTIFY_FROM`: dirección institucional emisora autorizada.
   - `KAWSAY_NOTIFY_TO`: correo del responsable designado por la institución (no alumnos).
   - `NODE_FUNCTION_ALLOW_BUILTIN=crypto`: el nodo Code necesita el módulo `crypto`.
   - `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`: solo en una instancia con acceso a workflows **restringido**.
4. Activar el workflow y copiar su **Production URL**, p. ej. `https://servidor-n8n.../webhook/kawsay-educativo`; no usar la URL temporal `webhook-test`.
5. En el entorno privado del **backend**, configurar:
   - `AUTOMATION_WEBHOOK_URL` con la URL del workflow.
   - `AUTOMATION_WEBHOOK_SECRET` con el mismo secreto.
   - `AUTOMATION_AUTO_DISPATCH=true` y `AUTOMATION_DISPATCH_INTERVAL_SECONDS=15`.
6. Reiniciar **solo cuando el almacenamiento del backend sea persistente y esté respaldado**. El bucle automático despacha eventos `PENDING` cada 15 s y realiza reintentos con backoff.
7. Probar con una cuenta de prueba autorizada: abrir un ejercicio, pedir dos pistas, revisar «Alertas educativas», confirmar ejecución de n8n, correo SMTP y estado del evento `DELIVERED`.

**El workflow no se activa ni envía correos por importarse en GitHub.** Sin SMTP o sin firma válida no informa éxito. Si falla SMTP, n8n no llega al nodo 200, y el backend conserva el evento hasta reintentar. Es entrega **al menos una vez**; el receptor externo debe deduplicar usando `event_id` si requiere evitar correos duplicados.

**Seguridad:** no subir credenciales o correos institucionales privados a GitHub. Mantener n8n y el backend con HTTPS y control de acceso. No emplear Render Free + SQLite efímera como almacén de registros reales de menores. La activación de `AUTOMATION_AUTO_DISPATCH` presupone **una sola instancia del backend**; desplegar varios procesos requiere una cola con leasing o exclusión mutua para evitar avisos duplicados.
