# 03 · Requisitos funcionales

Prioridad: **M**VP · **P**ost-MVP

| ID | Requisito | Pri |
|----|-----------|-----|
| RF-01 | Autenticación con access+refresh token, rotación y revocación | M |
| RF-02 | Docente provisiona estudiantes (código+PIN) y los asigna a aulas | M |
| RF-03 | Aula multigrado: N grados, cada estudiante con su grado | M |
| RF-04 | CRUD de currículo configurable (admin) e importación | M |
| RF-05 | Crear actividad base (área, tema, competencia, objetivo, contenido, preguntas) | M |
| RF-06 | Seleccionar múltiples grados y solicitar adaptación IA | M |
| RF-07 | Variantes en estado `draft→in_review→approved→published`; no se publica sin aprobación docente | M |
| RF-08 | Docente edita variantes; versionado de cambios | M |
| RF-09 | Creación manual de variantes sin IA (fallback) | M |
| RF-10 | Asignación a aula/estudiantes; cada estudiante recibe la variante de **su** grado (override docente posible) | M |
| RF-11 | Learning Packs versionados descargables por grado+materia | M |
| RF-12 | Ejecución offline de tareas y persistencia en SQLite | M |
| RF-13 | Registro de intentos (student, activity, question, answer, correct, n.º intento, pistas, tiempo, fecha) | M |
| RF-14 | Sync push/pull idempotente con ACK por evento | M |
| RF-15 | Progreso por competencia con metodología documentada | M |
| RF-16 | Motor adaptativo: pista→reintento→refuerzo→reevaluación; estados REFUERZO/ESPERADO/DESAFÍO internos | M |
| RF-17 | Detección de fortalezas y de necesidad de apoyo (support flags por reglas) | M |
| RF-18 | Alertas educativas con evidencia, enlace a progreso y registro de intervención | M |
| RF-19 | Intervenciones docentes y evolución observada posterior (sin afirmar causalidad) | M |
| RF-20 | "Quiero aprender" con materias del currículo configurado | M |
| RF-21 | Motivación basada en datos reales (comparación con historial) | M |
| RF-22 | Onboarding: nombre, grado, ubicación administrativa, lengua materna/variante, lengua preferida, intereses; sin inferir lengua por ubicación | M |
| RF-23 | Dashboard docente: progreso por estudiante/grado/competencia, intentos, pistas, evolución | M |
| RF-24 | Tutor KAWSAY guiado (explicar→ejemplo→preguntar→esperar→retroalimentar) | P |
| RF-25 | Contenido bilingüe verificado (palabra, imagen, audio, ejemplo) | P |
| RF-26 | Flujo de revisión de traducciones por especialistas | P |
| RF-27 | Reportes exportables | P |
| RF-28 | Auditoría de accesos a datos de estudiantes | M |
| RF-29 | Retención/eliminación configurable de datos | P |
