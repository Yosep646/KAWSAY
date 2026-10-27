# 06 · Diseño de base de datos (SQLite)

Decisión del autor (Yosep): **la base de datos es SQLite** (ADR-010). El esquema real está en `backend/migrations/versions/*_0001_*.py`
y el diagrama ER se genera desde los modelos (`07-er-diagram.md`). Aquí se explican las decisiones, no se repite la lista de columnas.

## Cómo está configurada SQLite
| Aspecto | Configuración | Por qué |
|---|---|---|
| Archivo | `backend/data/kawsay.db` (`DATABASE_URL`), permisos `600` en POSIX | contiene datos de menores |
| Modo | WAL, `synchronous=NORMAL`, `foreign_keys=ON`, `busy_timeout=15 s` | lecturas sin bloquear al escritor; integridad referencial real |
| Escrituras | toda transacción usa `BEGIN IMMEDIATE` | un solo escritor; evita «database is locked» al promover lectura→escritura |
| Fechas | tipo `UTCDateTime`: se guarda en UTC y se devuelve siempre con zona | SQLite no guarda zona horaria |
| JSON | tipo `JSON` (evidencias, opciones, respuestas) | portable |
| Identificadores | `UUID` (texto de 32 hex); `grades.id`/`languages.id` son `INTEGER` | `SMALLINT PRIMARY KEY` no autoincrementa en SQLite |
| Secuencias | tabla `counters` (`sa_seq`) para el cursor de `sync/pull` | SQLite no tiene secuencias; se incrementa dentro de la transacción de escritura |
| Migraciones | Alembic en modo *batch*, DDL transaccional | cada migración se aplica completa o no se aplica |

**Regla de código:** nunca mantener una transacción abierta durante llamadas lentas (IA, webhooks). El código hace `commit` antes; está
probado (`tests/test_concurrency_sqlite.py`: una llamada de 1.5 s a la IA no bloquea a otros usuarios).

## Grupos de tablas
| Grupo | Tablas |
|---|---|
| Identidad | `users` (rol único: STUDENT/TEACHER/ADMIN), `refresh_tokens`, `teacher_profiles`, `student_profiles` |
| Organización | `ugel_units`, `schools`, `classrooms`, `classroom_teachers`, `classroom_students` (el **grado** vive en el estudiante: aulas multigrado) |
| Currículo | `grades`, `curriculum_frameworks` (`is_demo` obligatorio), `subjects`, `competencies`, `capacities` |
| Planificación | `academic_years`, `school_curriculum_plans`, `curriculum_plan_versions` (estados + 1 ACTIVE por plan), `academic_periods`, `curriculum_units`, `curriculum_topics` |
| Contenido y tareas | `assignments`, `assignment_variants` (1 por grado, instantánea del objetivo), `questions`, `student_assignments` (origen TEACHER/SELF) |
| Aprendizaje | `learning_attempts` (append-only), `student_competency_progress` |
| Análisis | `support_flags`, `teacher_interventions` |
| Idiomas | `languages` (es, qu, ay), `language_variants`, `student_languages`, `variant_translations` (solo `VERIFIED` llega al estudiante) |
| IA y automatización | `ai_generation_requests` (sin contenido), `domain_events` (outbox), `sync_events` |
| Seguridad | `audit_log` |

## Garantías en la base de datos (no solo en el código)
- `learning_attempts`: triggers que impiden `UPDATE` y `DELETE` (evidencia educativa inmutable).
- `assignment_variants`: `APPROVED/PUBLISHED` exigen `approved_by` y `approved_at` (la IA no puede saltarse la aprobación docente);
  `source='AI'` exige `generated_by`.
- `curriculum_plan_versions`: índice único parcial → **una sola versión ACTIVE por plan**; aprobadas exigen aprobador.
- `support_flags`: índice único parcial → un solo flag activo por (estudiante, competencia, regla).
- `users`: CHECK de identidad (estudiante = código sin correo; docente/admin = correo sin código).
- `variant_translations`: `VERIFIED` exige `verified_by`.
- `sync_events.event_id` único → idempotencia de la sincronización, también para rechazos.
- Claves foráneas `RESTRICT` en todo el historial; solo `refresh_tokens` usa `CASCADE`.

## Límites de SQLite (honestidad)
Un único escritor: adecuado para un piloto de decenas de usuarios simultáneos en un solo servidor; **no** para varias réplicas del
backend ni para miles de escrituras por segundo. Camino de crecimiento: los modelos usan tipos portables (UUID, JSON, UTC); migrar a
PostgreSQL implicaría cambiar `database.py`, la migración inicial y las secuencias/trigger, pero no el dominio.
