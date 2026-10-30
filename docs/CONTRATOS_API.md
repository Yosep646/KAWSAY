# Contratos comprobados

Se reutilizan las rutas del respaldo; no se añadieron endpoints. El inventario previo está en [08-api.md](08-api.md) y [openapi.json](openapi.json). El código de rutas sigue siendo la referencia.

| Operación | Contrato usado |
|---|---|
| Acceso estudiante | `POST /api/v1/auth/student-login`: `login_code`, `pin`, `device_id` |
| Identidad remota | `GET /api/v1/auth/me`: `id`, `role`, `display_name` |
| Descarga | `GET /api/v1/sync/pull?cursor=0&limit=50`: `tasks`, `cursor`, `has_more`; avanzar solo si el cursor crece |
| Reanudar estado oficial | `GET /api/v1/sync/tasks/{id}/attempts?device_id={uuid}`: `questions` con `question_id`, `closed`, `device_attempt_number` |
| Enviar respuestas | `POST /api/v1/sync/push`: `device_id`, `events` de hasta 100 elementos |
| Resumen docente | `GET /api/v1/analytics/classrooms/{id}/summary` |
| Progreso docente | `GET /api/v1/analytics/classrooms/{id}/students/{student_id}/progress` |

Cada evento conserva su UUID, tipo `attempt.created`, asignación, pregunta, número de intento, respuesta, pistas, tiempo y fecha. El servidor determina al estudiante por autenticación y vuelve a corregir la respuesta. `ACKED` y `DUPLICATE` confirman el mismo UUID; `REJECTED` no confirma y el cliente nuevo conserva el evento para revisión. UUID repetido con contenido diferente se rechaza en el servicio existente.

El cliente nuevo valida longitud del lote de confirmación, UUID únicos, pertenencia al envío y estado reconocido antes de modificar la cola. Si la consulta del estado oficial falla después del ACK, conserva los eventos: el reintento idempotente resuelve el caso.

Cambio de autenticación: access tokens nuevos incluyen el claim obligatorio `sid`, UUID de familia de refresh. Cada petición autenticada exige una fila de esa familia perteneciente al usuario, vigente y no revocada. Una rotación conserva la familia; logout, reutilización de refresh antiguo y reset de PIN la revocan. Access tokens anteriores sin `sid` se rechazan; un refresh vigente puede emitir tokens del formato nuevo. No se cambió el JSON público de login ni las tablas.

Limitación: no se añadió gestión de revocación individual de dispositivos ni se vinculó el `device_id` del cuerpo a un nuevo claim; requiere diseño adicional. La revocación de sesiones probada no equivale a revocar instantáneamente una copia local sin conexión.
