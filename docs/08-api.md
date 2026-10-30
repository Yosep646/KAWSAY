# 08 · API REST (generada)

_Generada por `python scripts/gen_docs.py` desde OpenAPI. Documentación interactiva en `/docs` (solo fuera de producción)._

Versión **0.1.0** · 77 endpoints · prefijo `/api/v1` (sondas `/health`, `/ready` sin prefijo).

## Convenciones
- JSON; errores `{code, message, request_id, details?}`; sin trazas internas.
- Autenticación `Authorization: Bearer <access token>` (15 min) + refresh token con rotación.
- Roles: `STUDENT`, `TEACHER`, `ADMIN`. La autorización se valida en el servidor; los recursos ajenos responden **404** (no revelan existencia).
- Límite de payload 1 MiB; se exige `Content-Length` en POST/PUT/PATCH; rate limit en login, refresh, IA y tutor.

## Quién puede qué (resumen)
| Rol | Puede |
|---|---|
| ADMIN | usuarios, escuelas, UGEL, marcos curriculares, aprobar/activar planificaciones, verificar traducciones, auditoría, automatización |
| TEACHER | sus aulas y estudiantes, planificaciones de su escuela (borrador), actividades y variantes, adaptación con IA, publicación, alertas, intervenciones, analítica de sus aulas |
| STUDENT | iniciar sesión (código+PIN), `sync`, mis tareas, quiero aprender, tutor, mi progreso, mis idiomas |

## analytics
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/analytics/classrooms/{classroom_id}/forecast` | Forecast |
| `GET` | `/api/v1/analytics/classrooms/{classroom_id}/strengths` | Strengths |
| `GET` | `/api/v1/analytics/classrooms/{classroom_id}/students/{student_id}/progress` | Student Progress |
| `GET` | `/api/v1/analytics/classrooms/{classroom_id}/summary` | Classroom Summary |

## assignments
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/assignments` | List Mine |
| `POST` | `/api/v1/assignments` | Create |
| `GET` | `/api/v1/assignments/mine` | My Tasks |
| `GET` | `/api/v1/assignments/{assignment_id}` | Detail |
| `POST` | `/api/v1/assignments/{assignment_id}/adapt` | Adapt |
| `POST` | `/api/v1/assignments/{assignment_id}/publish` | Publish |
| `PATCH` | `/api/v1/assignments/{assignment_id}/variants/{variant_id}` | Patch Variant |
| `POST` | `/api/v1/assignments/{assignment_id}/variants/{variant_id}/approve` | Approve |
| `PUT` | `/api/v1/assignments/{assignment_id}/variants/{variant_id}/questions` | Put Questions |
| `POST` | `/api/v1/assignments/{assignment_id}/variants/{variant_id}/review` | Review |

## audit
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/audit-log` | List Audit |

## auth
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/auth/change-password` | Change Password |
| `POST` | `/api/v1/auth/login` | Login |
| `POST` | `/api/v1/auth/logout` | Logout |
| `GET` | `/api/v1/auth/me` | Me |
| `POST` | `/api/v1/auth/refresh` | Refresh |
| `POST` | `/api/v1/auth/student-login` | Student Login |

## automation
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/automation/dispatch` | Dispatch |
| `GET` | `/api/v1/automation/events` | List Events |
| `POST` | `/api/v1/automation/events/{event_id}/retry` | Retry Event |

## classrooms
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/classrooms` | List Mine |
| `POST` | `/api/v1/classrooms` | Create |
| `GET` | `/api/v1/classrooms/{classroom_id}` | Detail |

## curriculum
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/curriculum/frameworks` | List Frameworks |
| `POST` | `/api/v1/curriculum/frameworks` | Import Framework |
| `GET` | `/api/v1/curriculum/frameworks/{framework_id}` | Get Framework |
| `GET` | `/api/v1/curriculum/grades` | Grades |

## interventions
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/interventions` | Create |
| `GET` | `/api/v1/interventions` | List For Student |

## languages
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/assignments/{assignment_id}/variants/{variant_id}/translations` | Upsert Translation |
| `GET` | `/api/v1/languages` | List Languages |
| `POST` | `/api/v1/languages/variants` | Create Variant |
| `GET` | `/api/v1/students/me/languages` | My Languages |
| `PUT` | `/api/v1/students/me/languages` | Set My Languages |
| `GET` | `/api/v1/students/{student_id}/languages` | Get Student Languages |
| `PUT` | `/api/v1/students/{student_id}/languages` | Set Student Languages |
| `POST` | `/api/v1/translations/{translation_id}/reject` | Reject Translation |
| `POST` | `/api/v1/translations/{translation_id}/submit` | Submit Translation |
| `POST` | `/api/v1/translations/{translation_id}/verify` | Verify Translation |

## learning
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/learning/activities` | Activities |
| `POST` | `/api/v1/learning/start` | Start |
| `GET` | `/api/v1/learning/subjects` | Subjects |
| `GET` | `/api/v1/learning/topics` | Topics |

## ops
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Liveness: el proceso responde |
| `GET` | `/ready` | Readiness: dependencias disponibles |

## planning
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/planning/active` | Active For Classroom |
| `GET` | `/api/v1/planning/plans` | List Plans |
| `POST` | `/api/v1/planning/plans` | Create Plan |
| `POST` | `/api/v1/planning/plans/{plan_id}/versions` | New Version |
| `GET` | `/api/v1/planning/versions/{version_id}` | Get Version |
| `POST` | `/api/v1/planning/versions/{version_id}/activate` | Activate |
| `POST` | `/api/v1/planning/versions/{version_id}/approve` | Approve |
| `POST` | `/api/v1/planning/versions/{version_id}/periods` | Add Period |
| `POST` | `/api/v1/planning/versions/{version_id}/reject` | Reject |
| `POST` | `/api/v1/planning/versions/{version_id}/submit` | Submit |
| `POST` | `/api/v1/planning/versions/{version_id}/topics` | Add Topic |
| `POST` | `/api/v1/planning/versions/{version_id}/units` | Add Unit |

## progress
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/progress/me` | My Progress |
| `GET` | `/api/v1/progress/me/messages` | My Messages |

## schools
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/schools` | Create School |
| `GET` | `/api/v1/schools` | List Schools |
| `POST` | `/api/v1/schools/ugel-units` | Create Ugel |

## students
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/students` | Create |
| `GET` | `/api/v1/students/{student_id}` | Get One |
| `POST` | `/api/v1/students/{student_id}/reset-pin` | Reset Pin |

## support-flags
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/support-flags` | List Flags |
| `PATCH` | `/api/v1/support-flags/{flag_id}` | Patch Flag |

## sync
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/sync/pull` | Pull |
| `POST` | `/api/v1/sync/push` | Push |

## tutor
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/tutor/turn` | Turn |

## users
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/users` | Create User |
| `GET` | `/api/v1/users` | List Users |
| `PATCH` | `/api/v1/users/{user_id}` | Patch User |
