# Automatización (n8n) — estado: PROTOTIPO / importación verificada

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
