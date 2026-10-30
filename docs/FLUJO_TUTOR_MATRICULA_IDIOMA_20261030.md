# KAWSAY AI — Tutor, matrículas, cursos e idiomas (30 de octubre de 2026)

## Qué se ha implementado

### 1. Matrícula (docente)
- En `/estudiantes` se puede **registrar un alumno nuevo** con código/PIN o correo y contraseña.
- También se puede **matricular al mismo alumno en el aula del año escolar siguiente** si pertenecía a un aula previamente atendida por el mismo docente en la misma institución.
- Se conserva su cuenta, grado oficial, registro histórico y progreso. No se realiza una promoción automática de grado; eso requiere un proceso institucional explícito.
- Se valida que no haya otra matrícula activa para el mismo año; no se puede elegir una cuenta de otra escuela.
- Si el docente ya había publicado actividades para ese grado en el nuevo año, se entregan al estudiante durante la matrícula.
- API: `GET /api/v1/classrooms/{id}/eligible-students` y `POST /api/v1/classrooms/{id}/enrollments` (solo docente asignado).

### 2. Mis cursos (estudiante web/Flutter)
- `/estudiante/cursos` y `GET /api/v1/sync/courses`.
- Los cursos son áreas de la planificación escolar activa correspondientes a su grado y aula. Si aún no hay planificación ACTIVE, la lista estará vacía, **sin inventar materias**.
- El docente publica tareas con la competencia y grado adecuados y el estudiante las recibe por sincronización.
- Los cursos y actividades ya descargados permanecen consultables sin conexión. **La web necesita conservar la sesión abierta**: la recuperación de login desde cero en modo avión no está garantizada.

### 3. Tutor KAWSAY (estudiante)
- Dentro de una actividad se puede pedir hasta tres pistas. Con Internet utiliza `POST /api/v1/tutor/turn` y muestra explícitamente si procede de IA externa o reglas pedagógicas.
- El modelo externo de lenguaje es **opcional** y solo opera si el servidor está configurado con las credenciales autorizadas; el proveedor deshabilitado usa reglas, no una respuesta simulada.
- Si no hay red, la web usa las pistas educativas ya descargadas de esa tarea; Flutter usa reglas locales y pistas descargadas. **Nunca se ofrece una respuesta abierta de LLM offline** sin tener un modelo local compatible, que aún no está incorporado.
- No se entrega la respuesta correcta mientras el ejercicio está abierto. Se contabiliza el número de pistas en cada intento.
- Tras pedir al menos dos niveles de ayuda en una pregunta, el backend registra un evento único por pregunta para que el docente vea que el estudiante necesita acompañamiento.
- El evento se guarda en la outbox SQLite y aparece en `GET /api/v1/tutor/help-requests` para el docente autorizado, visible en Alertas educativas. El webhook n8n, si se configura, recibe un aviso firmado con HMAC **sin el ID del estudiante ni de la pregunta**.
- n8n es **secundario y opcional**: no es el tutor que genera respuestas. Los eventos esperan a ser enviados si no se configura el webhook.

### 4. Idioma (estudiante web/Flutter)
- La nueva sección `/estudiante/idioma` permite elegir idioma materno, variante declarada y preferencia de aprendizaje; backend: `GET/PUT /api/v1/students/me/languages`.
- Idiomas disponibles: español, quechua y aimara. No se infiere la lengua de la ubicación ni del nombre.
- Las traducciones educativas tienen que haber sido revisadas y **VERIFIED** por un humano. Si no hay traducción, se mantiene el contenido original del docente.
- Flutter guarda el catálogo descargado y la preferencia pendiente en SQLite, aun si no hay Internet, y la sincroniza antes de descargar nuevas traducciones al reconectarse.
- La web necesita red para guardar en el servidor; puede mostrar las actividades que ya fueron descargadas mientras estaba conectada.

## Qué función cumple ML (y qué falta)

**No atribuir al tutor una predicción ML que no existe.**
- El repositorio contiene un pipeline de ML separado para pronosticar dificultad con secuencias históricas de ejercicios.
- El registro actual incluye modelos **CANDIDATE entrenados con datos SYNTHETIC**, no aprobados, y la configuración de producción de Render **no lleva un ML validado**.
- Las recomendaciones educativas de reglas auditables funcionan con evidencias reales de intentos. Solo con un modelo de datos autorizados, compatible y **APPROVED** se podrá incorporar una probabilidad ML adicional al seguimiento docente.
- El modelo externo ASSISTments candidato de entrenamiento previo no comparte directamente la estructura de 11 variables de este pipeline; no es conectarlo y ya.
- La IA generativa del Tutor ayuda con pistas en línea cuando hay proveedor configurado; el modelo ML predice necesidad de acompañamiento, y n8n automatiza avisos. Son tres componentes diferentes.

## Pruebas

- Backend: `tests/test_enrollment_existing.py`, `tests/test_tutor_automation.py`, y las pruebas anteriores de cursos, tutor, traducciones y sincronización.
- Web: `src/test/studentCoreFeatures.test.tsx`.
- Flutter: `test/offline_language_test.dart` junto a `test/offline_sync_test.dart`.
- GitHub Actions: análisis, pruebas, pruebas de navegador y compilación APK.

## Consideraciones para la hackatón

La implementación soporta el flujo: **docente matricula → curso por grado/planteamiento ACTIVE → actividad publicada → estudiante la descarga → resuelve y pide pistas offline → sincroniza → docente detecta solicitudes de apoyo**.

Lo que **aún no puede afirmarse** sin pruebas adicionales: funcionamiento completo en un teléfono Android real en modo avión con cierre/reinicio; tutor de lenguaje natural local sin Internet; traducciones quechua/aimara no verificadas; modelo ML real aprobado para el aula; datos persistentes en Render Free; ni notificaciones externas n8n sin configuración activa.

**No desplegar en Render Free para aplicar estos cambios si existe alguna posibilidad de recuperar datos del SQLite anterior**: al reemplazar el contenedor se pueden perder. Primero asegurar el almacenamiento y recuperar copias.
