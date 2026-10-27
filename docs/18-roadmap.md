> **Estado al cierre:** fases 1–6, sync, Reto 10, IA (gateway), tutor, idiomas, automatización, ML experimental y panel docente: hechas y probadas.
> Pendientes: app Flutter compilada y probada offline en dispositivo, Learning Packs con medios, datos reales, modelo ML aprobado, E2E en navegador.
> Ver `00-repository-audit.md` para el estado exacto.

# 18 · Roadmap (propuesta con reordenamiento)

| Fase | Contenido | Criterio de salida |
|---|---|---|
| 0 | Documentación + ADRs (esta entrega) | Arquitectura aprobada |
| 1 | Repo, Docker, FastAPI, SQLite, health, Alembic, CI | `compose up` + `/health` + migración vacía + CI verde |
| 2 | Auth, roles, usuarios, refresh rotation | Tests authz/seguridad |
| 3 | Escuelas, aulas multigrado, estudiantes | Aula con 3 grados funcionando |
| 4 | Currículo (import/CRUD) | Competencias consultables |
| 5 | Actividades, preguntas, asignaciones, variantes **manuales** + flujo aprobar/publicar | Publicar y ver asignación correcta por grado |
| 6 | AI Gateway + adaptación multigrado | Variantes `draft` válidas; fallback manual |
| 7 | Flutter: login, home, mis tareas | Tarea visible |
| 8 | SQLite, Learning Packs | Tarea offline |
| 9 | Sync Engine | Prueba sección 51 verde |
| 11a | Attempts + Progress + Adaptive (**adelantada**) | Prueba sección 53 |
| 12 | Dashboard docente, analytics, flags, intervenciones | **Corte MVP docente→estudiante→dashboard** |
| 10 | "Quiero aprender" | Flujo completo con intentos/pistas |
| 13 | Tutor KAWSAY guiado | Sin entrega prematura de respuestas |
| 14 | Lenguas y aprendizaje bilingüe verificado | Prueba sección 54 |
| 15 | Hardening: seguridad, observabilidad, carga | Checklist seguridad |
| 16 | Deploy, optimización, piloto | Piloto con metas |

Cada fase entrega el informe de la sección 64 del prompt.
