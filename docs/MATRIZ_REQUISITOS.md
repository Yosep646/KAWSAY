# Matriz de trazabilidad del ZIP actualizado

Fecha: 30/10/2026. El resultado se limita al alcance indicado; la existencia de archivos no equivale a aceptación integral. Evidencia de comandos en [REPORTE_PRUEBAS.md](REPORTE_PRUEBAS.md). Los archivos de código y pruebas son rutas relativas a la raíz del proyecto.

| ID | Requisito y estado | Archivos / prueba ejecutada | Resultado y límite pendiente |
|---|---|---|---|
| RF-01 | Autenticación segura por rol — PARCIALMENTE IMPLEMENTADO | `backend/app/core/permissions.py`, `modules/auth/`; `tests/test_auth.py`, `test_security_hardening.py`, E2E acceso | Roles, expiración y revocación de familia probados; gestión individual de dispositivos y revisión completa pendientes. |
| RF-02 | Gestión institucional — PARCIALMENTE IMPLEMENTADO | `backend/app/modules/schools/`; `tests/test_platform.py`, demo HTTP | Escuela DEMO persistida; aislamiento administrativo integral no acreditado. |
| RF-03 | Gestión de docentes — PARCIALMENTE IMPLEMENTADO | `modules/users/`, `teachers/`; demo HTTP | Creación/login comprobados; gestión completa y pruebas de todos los cambios pendientes. |
| RF-04 | Gestión de estudiantes — PARCIALMENTE IMPLEMENTADO | `modules/students/`; `test_auth.py`, `test_authorization_and_multigrade.py` | Creación, acceso y PIN probados; administración integral y ciclo de matrícula pendientes. |
| RF-05 | Aulas multigrado — IMPLEMENTADO Y VERIFICADO | `modules/classrooms/`; `test_assignments.py`, `test_authorization_and_multigrade.py` | Aulas y asignación por grado comprobadas con cuentas ficticias. |
| RF-06 | Cursos y planificación — PARCIALMENTE IMPLEMENTADO | `modules/planning/`, `teacher-web/src/pages/Planning.tsx`; `test_planning.py` | Plan vigente por área/grado probado; módulo de cursos en ambos clientes incompleto. |
| RF-07 | Integración MINEDU — PENDIENTE | `modules/curriculum/`, `docs/00-repository-audit.md` | No se validó una matriz oficial por grado; marcos DEMO no son validación curricular. |
| RF-08 | Creación de actividades — IMPLEMENTADO Y VERIFICADO | `modules/assignments/`; `test_assignments.py`, demo y E2E offline | Actividad creada en API, preguntas persistidas y consumidas por estudiante. |
| RF-09 | Adaptación primero–sexto — PARCIALMENTE IMPLEMENTADO | `modules/ai/adaptation.py`, `domain/adaptive.py`; `test_ai_gateway.py` | Reglas y gateway probados en su alcance; no se acredita adaptación curricular integral 1–6. |
| RF-10 | Revisión/aprobación docente — IMPLEMENTADO Y VERIFICADO | `modules/assignments/service.py`; `test_assignments.py`, `test_ai_gateway.py` | Publicación exige variantes aprobadas y edición invalida aprobación. |
| RF-11 | Publicación/asignación — IMPLEMENTADO Y VERIFICADO | `modules/assignments/`; `test_assignments.py`, demo HTTP | Publicación asigna variante correspondiente al grado, sin sustitución por otro grado. |
| RF-12 | Mis cursos — PARCIALMENTE IMPLEMENTADO | `StudentHome.tsx`, `mobile/lib/features/assignments/tasks_screen.dart`; componentes y demo | Actividades reales por API; pantalla completa de cursos/matrícula no verificada. |
| RF-13 | Resolución — PARCIALMENTE IMPLEMENTADO | `StudentActivity.tsx`, `OfflineActivity.tsx`, Flutter ActivityScreen; E2E offline y Flutter | Diez respuestas web persistidas y corregidas en servidor; validación de todos los tipos y Android físico pendiente. |
| RF-14 | Evaluación de entrada — PENDIENTE | Módulos de actividades/progreso existentes | Sin ciclo diagnóstico equivalente ejecutado desde interfaces. |
| RF-15 | Evaluación de salida — PENDIENTE | Módulos de actividades/progreso existentes | Sin comparación pedagógicamente equivalente implementada y verificada. |
| RF-16 | Progreso — IMPLEMENTADO Y VERIFICADO | `modules/learning/`, `progress/`, `analytics/`; `test_sync_reto10.py`, E2E | Progreso derivado de respuestas persistidas y resumen docente comprobados. |
| RF-17 | Recomendaciones/refuerzos — PARCIALMENTE IMPLEMENTADO | `domain/adaptive.py`, `modules/forecast/`; `test_forecast.py`, `test_sync_reto10.py` | Reglas y guardas ML probadas; pertinencia pedagógica integral pendiente. |
| RF-18 | Alertas con evidencia — IMPLEMENTADO Y VERIFICADO | `modules/support_flags/`, `FlagCard.tsx`; `test_sync_reto10.py`, E2E docente | Evidencia real DEMO y decisión docente; sin diagnóstico ni atribución causal. |
| RF-19 | Persistencia offline — PARCIALMENTE IMPLEMENTADO | `offlineVault.ts`, `offlineLearning.ts`; `offline-e2e/learning.spec.ts`, Flutter tests | Web con diez respuestas tras reinicio completo probada; móvil con API falsa, sin cierre de proceso físico. |
| RF-20 | Sync idempotente — IMPLEMENTADO Y VERIFICADO | `modules/sync/`; `test_sync_reto10.py`, `test_concurrency_sqlite.py`, E2E offline | UUID duplicados no crean otra respuesta; ACK individual y SQLite únicos comprobados. No sustituye pruebas de todos los dispositivos. |
| RF-21 | Seguridad local — PARCIALMENTE IMPLEMENTADO | `offlineVault.ts`; `e2e/vault.spec.ts` | Nuevo almacén web cifrado y concurrencia probados; cola web anterior y SQLite móvil no cifrados. |
| RF-22 | Android — PENDIENTE | `mobile/`; Flutter analyze/test | Código y pruebas locales válidos; adb falló por permisos, sin APK generado ni prueba física. |
| RF-23 | Recursos lingüísticos verificados — PARCIALMENTE IMPLEMENTADO | `modules/languages/`; `test_automation_languages_tutor.py`, E2E idioma | Preferencias y guardas de traducción verificadas; revisión de los materiales por especialistas pendiente. |
| RF-24 | Entrenamiento/evaluación ML — IMPLEMENTADO Y VERIFICADO | `ml/`; `ml/tests/test_ml_pipeline.py` | 17 pruebas del pipeline experimental aprobadas; no acredita datos reales ni impacto pedagógico. |
| RF-25 | Modelos aprobados — PARCIALMENTE IMPLEMENTADO | `modules/forecast/service.py`, `ml/registry.py`; `test_forecast.py` | Restricciones de aprobación probadas con fixtures; modelo real validado BLOQUEADO POR DEPENDENCIA EXTERNA. |
| RF-26 | Automatización — PARCIALMENTE IMPLEMENTADO | `modules/automation/`, `automation/n8n/`; tests backend | Eventos internos probados; receptor y notificación n8n reales no ejecutados. |
| RF-27 | Auditoría — PARCIALMENTE IMPLEMENTADO | `modules/audit/`, tests de seguridad | Registros existentes comprobados en suite; revisión completa de accesos y retención pendiente. |
| RF-28 | Responsive — PARCIALMENTE IMPLEMENTADO | `teacher-web/src/styles.css`; E2E escritorio/móvil | Acceso y panel docente sin desbordamiento probados; dispositivos modestos y todas las vistas pendientes. |
| RF-29 | Recuperación/respaldos — PARCIALMENTE IMPLEMENTADO | `offlineVault.ts`, `mobile/app_database.dart`, `scripts/dev.py`; E2E y Flutter | Reapertura web y recuperación SQLite local probadas; recuperación de respaldo cifrado e interrupciones físicas pendientes. |
| RF-30 | Pruebas/documentación integral — PARCIALMENTE IMPLEMENTADO | `docs/`, suites backend/web/ML/Flutter | Evidencia de esta fase registrada; escenarios físicos, educativos y externos pendientes. |
