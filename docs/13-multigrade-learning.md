# 13 · Aprendizaje multigrado

1. El docente crea la **actividad base** y elige grados (`assignment_grades`).
2. `POST /assignments/{id}/adapt` crea una variante `draft` por grado (IA o manual).
3. Revisión/edición por variante (`in_review`); aprobación explícita por variante (`approved_by`).
4. `publish` solo si **todas las variantes seleccionadas** están aprobadas (o el docente descarta explícitamente un grado).
5. Al publicar se generan `student_assignments`: variante = la del **grado del estudiante**. Si no existe variante para su grado, el estudiante NO recibe nada y el docente ve la advertencia (nunca se asigna "la más cercana" en silencio).
6. Override individual (p. ej. estudiante que trabaja un grado distinto): explícito, con `override_by` y auditado.
7. Test automatizado (sección 52): un alumno de 1.º jamás recibe la variante de 3.º; test a nivel de repositorio, API y sync pull.

Adaptación IA: vocabulario, complejidad, longitud, pasos, números, instrucciones, ejemplos, apoyos y dificultad; el `OutputValidator` verifica que se conserve competencia y objetivo.
