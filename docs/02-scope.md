# 02 · Alcance

## Dentro del MVP
- Login docente/estudiante; roles STUDENT/TEACHER/ADMIN.
- Escuelas, aulas multigrado, estudiantes con grado individual.
- Currículo configurable (grados, áreas, competencias, capacidades).
- Actividades y preguntas (tipos iniciales: opción múltiple, respuesta numérica corta, texto corto verificable).
- Adaptación multigrado vía AI Gateway con flujo crear→proponer→revisar→editar→aprobar→publicar.
- App Android estudiante: tareas offline, SQLite, Learning Packs, sync push/pull idempotente.
- "Quiero aprender": materia→tema→forma→actividad→intentos→pistas→progreso.
- Registro de intentos, progreso por competencia, support flags, recomendaciones, intervenciones.
- Dashboard docente web responsive.
- Español como idioma de interfaz y contenido; preparación del modelo para quechua/aimara.

## Fuera del MVP (post-MVP)
iOS/Windows/macOS, panel de administración completo, docente offline (PWA), LLM on-device, voz/ASR, Redis/workers, n8n, notificaciones push, reportes PDF avanzados, interoperabilidad con sistemas del ministerio.

## Supuestos
Un solo país/currículo en el piloto; contenido lingüístico indígena solo cuando exista versión verificada; dispositivos Android de gama baja (≥ 2 GB RAM).

## No-objetivos
Reemplazar al docente; diagnosticar psicológicamente; calificaciones oficiales; recopilar datos innecesarios.
