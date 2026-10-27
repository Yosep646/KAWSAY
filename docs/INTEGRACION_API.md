# Integración HTTP y sincronización

Referencia de endpoints: [08-api.md](08-api.md).
Contrato generado de la aplicación: [openapi.json](openapi.json).
Regenerar con `python scripts/gen_docs.py` desde la raíz.

## Configuración y autenticación

- React: `VITE_API_URL`; vacío usa el mismo origen y el proxy Vite configurado.
- Flutter: `--dart-define=KAWSAY_API=http://10.0.2.2:8000` para emulador Android.
- Prefijo `/api/v1`; sondas públicas `GET /health` y `GET /ready`.
- HTTPS en entorno externo. CORS del servidor es una lista explícita.
- `POST /auth/login`: `{ "email": "<correo>", "password": "<contraseña>" }`.
- `POST /auth/student-login`: `{ "login_code": "<código>", "pin": "<PIN>", "device_id": "<UUID>" }`.
- Respuesta de login: `access_token`, `refresh_token`, `expires_in`, `user`.
- Recursos protegidos: `Authorization: Bearer <access_token>`.
- `POST /auth/refresh`: `{ "refresh_token": "<token>" }`; rota ambos tokens.
- `POST /auth/logout`: mismo cuerpo para revocar el refresh.

El cliente web conserva access en memoria y refresh en sessionStorage. Flutter
usa almacenamiento seguro del sistema. No incluir tokens en logs. Un 503 o
problema de red durante refresh conserva la sesión; un 401 definitivo exige
identificarse. El cliente web admite `api.get(path, {signal, timeoutMs})`.
El timeout por defecto es 15 segundos por solicitud HTTP.

## Actividades y docentes

El flujo existente es aula → planificación activa → actividad y variantes por
grado → revisión → aprobación → publicación. Contenido generado por IA no se
publica directamente. `GET /analytics/classrooms/{id}/summary` devuelve los
conteos calculados; alertas en `GET /support-flags?classroom_id={id}`.
El backend limita propiedad por docente/escuela. No confiar en ocultar botones
como autorización.

## Pull incremental del estudiante

`GET /sync/pull?cursor=0&limit=20` requiere rol STUDENT y devuelve:

```json
{
  "tasks": [],
  "progress": [],
  "cursor": 0,
  "has_more": false,
  "server_time": "<ISO-8601 UTC>"
}
```

Los arrays vacíos son ilustrativos, no datos de producción. Las tareas incluyen
contenido, preguntas, respuestas y pistas para corrección local; **no son un
formato de examen seguro contra lectura de respuestas**. El servidor recalifica
cada intento. Solo llegan traducciones verificadas. El cliente guarda el cursor
después de guardar contenido y progreso; ante interrupción puede repetir la
página. Las actualizaciones son idempotentes. No avanzar el cursor si falla el
guardado o si el servidor devuelve un cursor inválido.

## Push y confirmaciones

`POST /sync/push`, rol STUDENT, entre 1 y 100 eventos:

```json
{
  "device_id": "<UUID-dispositivo>",
  "events": [{
    "event_id": "<UUID-persistido-del-intento>",
    "type": "attempt.created",
    "payload": {
      "student_assignment_id": "<UUID-asignación>",
      "question_id": "<UUID-pregunta>",
      "attempt_number": 1,
      "answer": {"index": 0},
      "is_correct": false,
      "hints_used": 0,
      "response_time_ms": 1500,
      "client_created_at": "<ISO-8601 UTC>"
    }
  }]
}
```

Los identificadores entre `<...>` deben sustituirse por UUID válidos. `answer`
es `{index: int}`, `{value: number}` o `{text: string}` según pregunta.
`is_correct` del cliente no es confiable: el servidor lo recalcula.

Respuesta: `{"results":[{"event_id":"<UUID>","status":"ACKED"}]}`.
Estados de servidor: ACKED, DUPLICATE, REJECTED (con `reason`). Solo los dos
primeros confirman recepción. El móvil ahora valida que haya exactamente una
confirmación por evento enviado y actualiza el lote en una transacción.
Respuestas incompletas o inválidas vuelven a PENDING con backoff, nunca SYNCED.
Reintentar utiliza el **mismo event_id**, no un UUID nuevo.

Motivos `duplicate_or_conflict` y `event_id_conflict` se conservan localmente
como CONFLICT; otros rechazos como FAILED. No se borran ni sobrescriben intentos.
Un UUID ya confirmado solo devuelve DUPLICATE si el contenido del intento coincide
con el guardado; si cambia, devuelve `event_id_conflict` y no confirma el nuevo trabajo.
La interfaz completa de resolución docente de conflictos queda pendiente.

## Errores

Formato de aplicación: `{code, message, request_id, details?}`.

| Estado | Significado / acción |
|---|---|
| 401 | Renovar una vez; si refresh también es 401, iniciar sesión |
| 403 | Rol no autorizado; no reintentar como error de red |
| 404 | Recurso inexistente o ajeno |
| 409 | Conflicto; conservar trabajo y solicitar revisión |
| 413 / 422 | Tamaño o validación; corregir entrada |
| 429 | Límite temporal; esperar, no bucle inmediato |
| 503 / fallo de red / timeout | Conservar cola; backoff y reintento |
| JSON inválido | Error de protocolo; no mostrar HTML interno ni confirmar operaciones |

## ML

`GET /analytics/classrooms/{id}/forecast` requiere propietario docente o permisos
administrativos. Sin modelo aprobado: `available=false`, `reason` e `items=[]`;
siguen operativas las alertas por reglas. El modo experimental es explícito y
muestra advertencia. Ítems incluyen `model_id`, `model_status`, probabilidad,
umbral, advertencia, finalidad orientativa e `inference_ms`.

## Automatización

`POST /automation/events/{event_id}/retry` requiere ADMIN y devuelve el ID y
`status: PENDING` al reencolar un evento FAILED. Un ID inexistente devuelve 404;
un evento que no esté en FAILED devuelve 409. El reencolado queda auditado y
mantiene el ID original: el destinatario debe evitar procesar dos veces el mismo
evento. Sin canal de notificación configurado no se acredita el envío de alertas.

Hay validaciones de entrada Pydantic en APIs; varios endpoints todavía devuelven
diccionarios sin `response_model` completo. El OpenAPI generado refleja esa
limitación y no garantiza por sí solo compatibilidad de todos los consumidores.
