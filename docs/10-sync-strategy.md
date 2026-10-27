# 10 · Estrategia de sincronización

## Modelo
Event-sourced para datos de aprendizaje: el cliente emite **eventos inmutables** con `event_id` (UUIDv7 cliente), `device_id`, `client_seq` (monótono por dispositivo), `type`, `payload`, `schema_version`.

## PUSH
`sync_queue(PENDING) → POST /sync/push (lotes ≤ 100, gzip)`. El servidor, por evento y en transacción:
1. valida esquema y autorización (el evento pertenece al estudiante/dispositivo autenticado);
2. `INSERT ... ON CONFLICT (device_id,event_id) DO NOTHING` → si ya existía responde `DUPLICATE` (cuenta como ACK);
3. aplica efecto (insertar intento, etc.), recalcula progreso;
4. devuelve por evento: `ACKED | DUPLICATE | REJECTED(code)`.
El cliente marca `SYNCED` solo con ACK/DUPLICATE; `REJECTED` va a `FAILED` con motivo visible para soporte; errores de red → reintento con backoff exponencial + jitter. Un evento nunca se borra de la cola antes del ACK.

## PULL
`GET /sync/pull?cursor=N` devuelve cambios con `server_seq > N` (asignaciones publicadas, packs nuevos, progreso oficial, recomendaciones, perfil), paginados; el cliente aplica en una transacción y guarda el nuevo cursor.

## Política de conflictos por entidad
| Entidad | Política |
|---|---|
| `learning_attempt` | append-only; idempotente por `id`; nunca se sobrescribe |
| `learning_session` | merge por `id`; fin de sesión = máximo `ended_at` |
| `profile` (estudiante) | versionado optimista (`version`); campos edit. por estudiante: lengua preferida/intereses → last-write-wins por campo con `server_received_at`; grado/aula: solo docente (servidor gana) |
| `assignment` / variante | **versión publicada inmutable**; cambios = nueva versión; el cliente conserva la versión con la que empezó hasta terminar |
| `progress` | derivado en servidor; local es provisional y se reemplaza en pull |
| `support_flag`, `recommendation` | solo servidor → cliente docente |

## Orden y tiempo
No se confía en el reloj del dispositivo: se guarda `client_created_at` informativo y `received_at` servidor. El orden causal es `(device_id, client_seq)`.

## Fallos y seguridad
Dispositivo revocado → push rechazado (401), datos locales se conservan hasta re-vincular. Límite de edad de evento configurable. Tamaño máximo de lote. Todo rechazo auditado.

## Pruebas
Duplicado exacto, reordenamiento, lote parcial, corte de red a mitad, dispositivo revocado, reloj adelantado, dos dispositivos del mismo estudiante.
