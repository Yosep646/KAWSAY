# 09 · Arquitectura offline

## Principios
Toda interacción de estudiante lee/escribe **primero en SQLite**. La red solo sincroniza. La app nunca bloquea una actividad por falta de red.

## SQLite local (cifrado)
Tablas: `profile`, `subjects`, `lessons`, `activities`, `assignments`, `questions`, `attempts`, `progress`, `learning_packs`, `hint_bank`, `sync_queue`, `meta(schema_version, last_pull_cursor)`.
Migraciones locales versionadas (`PRAGMA user_version`). Multi-perfil por dispositivo con desbloqueo local (PIN).

## Learning Packs
Paquete = `manifest.json` (id, versión, grado, materia, hash, tamaño, idiomas) + `lessons/activities/questions` + `media/` (imágenes WebP, audio Opus). Descarga reanudable, verificación SHA-256, instalación atómica (nuevo pack se activa solo si es íntegro), actualización diferencial por versión, borrado de packs antiguos.

## Qué funciona offline / online
| Offline | Online |
|---|---|
| Tareas descargadas, ejercicios, pistas pregeneradas, reglas adaptativas ligeras, progreso provisional, mensajes de motivación basados en historial, navegación | Generación/adaptación IA, tutor conversacional, análisis complejo, recomendaciones avanzadas, descarga/actualización de contenido |

## Interfaz para IA on-device futura
`LocalModelProvider` (interfaz Dart) con `isAvailable()` y `generateHint()`; hoy sin implementación → degradación a banco de pistas.

## Pruebas obligatorias
Escenario sección 51 del prompt como test E2E automatizado + test de crash (matar proceso durante escritura).
