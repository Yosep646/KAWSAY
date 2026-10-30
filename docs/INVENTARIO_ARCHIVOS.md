# Inventario estructural por archivo

Inventario y análisis estructural, no auditoría semántica completa

Los secretos se excluyen sin leerlos. Las coincidencias de hash no autorizan eliminaciones.

| Ruta | Tamaño (bytes) | Evidencia |
|---|---:|---|
| `.env.example` | 1110 | inventariado; revisión funcional no demostrada |
| `.github/workflows/ci.yml` | 1201 | inventariado; revisión funcional no demostrada |
| `.gitignore` | 507 | inventariado; revisión funcional no demostrada |
| `.vscode/extensions.json` | 167 | JSON válido; no certifica contrato |
| `.vscode/launch.json` | 840 | JSON válido; no certifica contrato |
| `.vscode/settings.json` | 404 | JSON válido; no certifica contrato |
| `.vscode/tasks.json` | 727 | JSON válido; no certifica contrato |
| `ai/README.md` | 298 | inventariado; revisión funcional no demostrada |
| `automation/n8n/workflows/01_support_flag_notify.json` | 3474 | JSON válido; no certifica contrato |
| `automation/README.md` | 1700 | inventariado; revisión funcional no demostrada |
| `backend/.dockerignore` | 74 | inventariado; revisión funcional no demostrada |
| `backend/alembic.ini` | 431 | inventariado; revisión funcional no demostrada |
| `backend/app/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/cli.py` | 3060 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/config.py` | 2255 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/database.py` | 2838 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/exceptions.py` | 2550 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/logging.py` | 1150 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/middleware.py` | 3090 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/password_policy.py` | 1499 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/permissions.py` | 1497 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/rate_limit.py` | 1159 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/security.py` | 2365 | sintaxis Python válida; no certifica ejecución |
| `backend/app/core/types.py` | 756 | sintaxis Python válida; no certifica ejecución |
| `backend/app/domain/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/domain/adaptive.py` | 9053 | sintaxis Python válida; no certifica ejecución |
| `backend/app/main.py` | 3192 | sintaxis Python válida; no certifica ejecución |
| `backend/app/models_registry.py` | 1618 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/ai/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/ai/adaptation.py` | 4894 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/ai/gateway.py` | 4410 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/ai/models.py` | 1234 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/ai/validators.py` | 4467 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/analytics/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/analytics/routes.py` | 6062 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/assignments/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/assignments/models.py` | 7508 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/assignments/routes.py` | 6806 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/assignments/schemas.py` | 1930 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/assignments/service.py` | 14929 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/audit/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/audit/models.py` | 861 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/audit/routes.py` | 1009 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/audit/service.py` | 513 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/auth/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/auth/models.py` | 1086 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/auth/routes.py` | 1854 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/auth/schemas.py` | 930 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/auth/service.py` | 6231 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/automation/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/automation/dispatch.py` | 3375 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/automation/events.py` | 577 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/automation/models.py` | 1366 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/automation/routes.py` | 1127 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/classrooms/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/classrooms/models.py` | 2023 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/classrooms/routes.py` | 2160 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/classrooms/service.py` | 3285 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/curriculum/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/curriculum/models.py` | 3119 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/curriculum/routes.py` | 4764 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/forecast/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/forecast/service.py` | 3280 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/health/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/health/routes.py` | 983 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/interventions/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/interventions/models.py` | 1143 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/interventions/routes.py` | 3959 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/languages/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/languages/models.py` | 3431 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/languages/routes.py` | 9573 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/learning/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/learning/models.py` | 3173 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/learning/routes.py` | 4880 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/learning/service.py` | 4496 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/planning/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/planning/models.py` | 5319 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/planning/routes.py` | 4887 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/planning/service.py` | 11720 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/progress/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/progress/routes.py` | 2020 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/schools/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/schools/models.py` | 1300 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/schools/routes.py` | 2770 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/students/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/students/models.py` | 668 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/students/routes.py` | 2086 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/students/service.py` | 2675 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/support_flags/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/support_flags/models.py` | 1633 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/support_flags/routes.py` | 4240 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/sync/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/sync/models.py` | 1051 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/sync/routes.py` | 1418 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/sync/service.py` | 9880 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/teachers/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/teachers/models.py` | 419 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/tutor/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/tutor/routes.py` | 1109 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/tutor/service.py` | 5493 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/users/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/users/models.py` | 1731 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/users/routes.py` | 1138 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/users/schemas.py` | 977 | sintaxis Python válida; no certifica ejecución |
| `backend/app/modules/users/service.py` | 2270 | sintaxis Python válida; no certifica ejecución |
| `backend/app/shared/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/workers/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/app/workers/dispatcher.py` | 793 | sintaxis Python válida; no certifica ejecución |
| `backend/data/.gitkeep` | 0 | binario/datos preservados; contenido no inspeccionado |
| `backend/data/kawsay.db` | 585728 | binario/datos preservados; contenido no inspeccionado |
| `backend/data/kawsay.db-shm` | 32768 | binario/datos preservados; contenido no inspeccionado |
| `backend/data/kawsay.db-wal` | 626272 | binario/datos preservados; contenido no inspeccionado |
| `backend/Dockerfile` | 614 | inventariado; revisión funcional no demostrada |
| `backend/migrations/env.py` | 972 | sintaxis Python válida; no certifica ejecución |
| `backend/migrations/script.py.mako` | 468 | inventariado; revisión funcional no demostrada |
| `backend/migrations/versions/20261019_0001_esquema_inicial_sqlite.py` | 42831 | sintaxis Python válida; no certifica ejecución |
| `backend/pyproject.toml` | 341 | inventariado; revisión funcional no demostrada |
| `backend/requirements-dev.txt` | 59 | inventariado; revisión funcional no demostrada |
| `backend/requirements.txt` | 208 | inventariado; revisión funcional no demostrada |
| `backend/tests/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/conftest.py` | 4721 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/fakes.py` | 1969 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_ai_gateway.py` | 10102 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_assignments.py` | 11807 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_auth.py` | 5670 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_authorization_and_multigrade.py` | 6082 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_automation_languages_tutor.py` | 15495 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_concurrency_sqlite.py` | 3813 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_domain_adaptive.py` | 3442 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_forecast.py` | 5662 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_health.py` | 1345 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_learn.py` | 3554 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_planning.py` | 9481 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_platform.py` | 1899 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_rule_vectors.py` | 1364 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_security_hardening.py` | 8938 | sintaxis Python válida; no certifica ejecución |
| `backend/tests/test_sync_reto10.py` | 12240 | sintaxis Python válida; no certifica ejecución |
| `database/README.md` | 883 | inventariado; revisión funcional no demostrada |
| `docker-compose.yml` | 1514 | inventariado; revisión funcional no demostrada |
| `docs/00-analisis-riesgos.md` | 5095 | inventariado; revisión funcional no demostrada |
| `docs/00-repository-audit.md` | 7677 | inventariado; revisión funcional no demostrada |
| `docs/01-vision.md` | 1747 | inventariado; revisión funcional no demostrada |
| `docs/02-scope.md` | 1408 | inventariado; revisión funcional no demostrada |
| `docs/03-functional-requirements.md` | 2596 | inventariado; revisión funcional no demostrada |
| `docs/04-non-functional-requirements.md` | 1707 | inventariado; revisión funcional no demostrada |
| `docs/05-architecture.md` | 2794 | inventariado; revisión funcional no demostrada |
| `docs/06-database-design.md` | 4158 | inventariado; revisión funcional no demostrada |
| `docs/07-er-diagram.md` | 12721 | inventariado; revisión funcional no demostrada |
| `docs/08-api.md` | 7163 | inventariado; revisión funcional no demostrada |
| `docs/09-offline-architecture.md` | 1554 | inventariado; revisión funcional no demostrada |
| `docs/10-sync-strategy.md` | 2466 | inventariado; revisión funcional no demostrada |
| `docs/11-ai-architecture.md` | 1941 | inventariado; revisión funcional no demostrada |
| `docs/12-adaptive-learning.md` | 2017 | inventariado; revisión funcional no demostrada |
| `docs/13-multigrade-learning.md` | 1101 | inventariado; revisión funcional no demostrada |
| `docs/14-security.md` | 3734 | inventariado; revisión funcional no demostrada |
| `docs/15-privacy.md` | 1113 | inventariado; revisión funcional no demostrada |
| `docs/16-testing.md` | 5084 | inventariado; revisión funcional no demostrada |
| `docs/17-deployment.md` | 1250 | inventariado; revisión funcional no demostrada |
| `docs/18-roadmap.md` | 1827 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-001-Flutter.md` | 718 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-002-FastAPI.md` | 523 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-003-PostgreSQL.md` | 514 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-004-SQLite-Offline.md` | 483 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-005-React-TypeScript.md` | 521 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-006-AI-Gateway.md` | 547 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-007-Offline-First.md` | 629 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-008-Monolito-Modular.md` | 509 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-009-Cuentas-Estudiantes.md` | 440 | inventariado; revisión funcional no demostrada |
| `docs/19-decisions/ADR-010-SQLite-servidor.md` | 1075 | inventariado; revisión funcional no demostrada |
| `docs/ai.md` | 1493 | inventariado; revisión funcional no demostrada |
| `docs/AUDITORIA_TECNICA.md` | 13045 | inventariado; revisión funcional no demostrada |
| `docs/GUIA_VSCODE.md` | 4793 | inventariado; revisión funcional no demostrada |
| `docs/INTEGRACION_API.md` | 5281 | inventariado; revisión funcional no demostrada |
| `docs/LIMPIEZA_REPOSITORIO.md` | 3356 | inventariado; revisión funcional no demostrada |
| `docs/ml-model-card.md` | 3844 | inventariado; revisión funcional no demostrada |
| `docs/ml.md` | 2176 | inventariado; revisión funcional no demostrada |
| `docs/openapi.json` | 141731 | JSON válido; no certifica contrato |
| `docs/VERIFICACION_2026-10-26.md` | 3249 | inventariado; revisión funcional no demostrada |
| `infrastructure/README.md` | 328 | inventariado; revisión funcional no demostrada |
| `ml/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `ml/common.py` | 1267 | sintaxis Python válida; no certifica ejecución |
| `ml/export_real.py` | 3795 | sintaxis Python válida; no certifica ejecución |
| `ml/features.py` | 4147 | sintaxis Python válida; no certifica ejecución |
| `ml/make_model_card.py` | 6020 | sintaxis Python válida; no certifica ejecución |
| `ml/models/kawsay-diff-20261021201327-fe6b38.joblib` | 2002353 | binario/datos preservados; contenido no inspeccionado |
| `ml/models/kawsay-diff-20261026203213-cce4aa.joblib` | 312209 | binario/datos preservados; contenido no inspeccionado |
| `ml/predict.py` | 1665 | sintaxis Python válida; no certifica ejecución |
| `ml/registry/registry.json` | 1535 | JSON válido; no certifica contrato |
| `ml/registry.py` | 1495 | sintaxis Python válida; no certifica ejecución |
| `ml/reports/kawsay-diff-20261021201327-fe6b38.json` | 4143 | JSON válido; no certifica contrato |
| `ml/reports/kawsay-diff-20261026203213-cce4aa.json` | 3353 | JSON válido; no certifica contrato |
| `ml/reports/robustness.json` | 3155 | JSON válido; no certifica contrato |
| `ml/requirements.txt` | 47 | inventariado; revisión funcional no demostrada |
| `ml/robustness.py` | 1921 | sintaxis Python válida; no certifica ejecución |
| `ml/synthetic.py` | 2162 | sintaxis Python válida; no certifica ejecución |
| `ml/tests/__init__.py` | 0 | sintaxis Python válida; no certifica ejecución |
| `ml/tests/test_ml_pipeline.py` | 7827 | sintaxis Python válida; no certifica ejecución |
| `ml/train.py` | 11483 | sintaxis Python válida; no certifica ejecución |
| `mobile/analysis_options.yaml` | 92 | inventariado; revisión funcional no demostrada |
| `mobile/lib/app/app.dart` | 596 | inventariado; revisión funcional no demostrada |
| `mobile/lib/app/session.dart` | 2192 | inventariado; revisión funcional no demostrada |
| `mobile/lib/app/theme.dart` | 760 | inventariado; revisión funcional no demostrada |
| `mobile/lib/core/api/api_client.dart` | 5947 | inventariado; revisión funcional no demostrada |
| `mobile/lib/core/config.dart` | 436 | inventariado; revisión funcional no demostrada |
| `mobile/lib/core/data/repository.dart` | 11119 | inventariado; revisión funcional no demostrada |
| `mobile/lib/core/database/app_database.dart` | 3316 | inventariado; revisión funcional no demostrada |
| `mobile/lib/core/network/connectivity_monitor.dart` | 930 | inventariado; revisión funcional no demostrada |
| `mobile/lib/core/offline/rules.dart` | 4823 | inventariado; revisión funcional no demostrada |
| `mobile/lib/core/security/token_store.dart` | 699 | inventariado; revisión funcional no demostrada |
| `mobile/lib/core/sync/sync_manager.dart` | 5963 | inventariado; revisión funcional no demostrada |
| `mobile/lib/features/assignments/activity_screen.dart` | 5939 | inventariado; revisión funcional no demostrada |
| `mobile/lib/features/assignments/tasks_screen.dart` | 1821 | inventariado; revisión funcional no demostrada |
| `mobile/lib/features/auth/login_screen.dart` | 2225 | inventariado; revisión funcional no demostrada |
| `mobile/lib/features/home/home_screen.dart` | 3578 | inventariado; revisión funcional no demostrada |
| `mobile/lib/features/learn/learn_screen.dart` | 4769 | inventariado; revisión funcional no demostrada |
| `mobile/lib/features/progress/progress_screen.dart` | 2004 | inventariado; revisión funcional no demostrada |
| `mobile/lib/features/settings/settings_screen.dart` | 4879 | inventariado; revisión funcional no demostrada |
| `mobile/lib/main.dart` | 1360 | inventariado; revisión funcional no demostrada |
| `mobile/lib/shared/widgets/big_button.dart` | 987 | inventariado; revisión funcional no demostrada |
| `mobile/pubspec.yaml` | 615 | inventariado; revisión funcional no demostrada |
| `mobile/README.md` | 2113 | inventariado; revisión funcional no demostrada |
| `mobile/test/offline_sync_test.dart` | 5215 | inventariado; revisión funcional no demostrada |
| `mobile/test/rules_test.dart` | 2487 | inventariado; revisión funcional no demostrada |
| `README.md` | 3968 | inventariado; revisión funcional no demostrada |
| `scripts/audit_inventory.py` | 3947 | sintaxis Python válida; no certifica ejecución |
| `scripts/browser_e2e.py` | 5513 | sintaxis Python válida; no certifica ejecución |
| `scripts/demo_e2e.py` | 9746 | sintaxis Python válida; no certifica ejecución |
| `scripts/dev.py` | 5934 | sintaxis Python válida; no certifica ejecución |
| `scripts/gen_docs.py` | 5068 | sintaxis Python válida; no certifica ejecución |
| `scripts/gen_rule_vectors.py` | 3131 | sintaxis Python válida; no certifica ejecución |
| `scripts/run_local.sh` | 804 | inventariado; revisión funcional no demostrada |
| `shared/rules_vectors.json` | 8627 | JSON válido; no certifica contrato |
| `teacher-web/.gitignore` | 20 | inventariado; revisión funcional no demostrada |
| `teacher-web/Dockerfile` | 232 | inventariado; revisión funcional no demostrada |
| `teacher-web/e2e/run.cjs` | 532 | inventariado; revisión funcional no demostrada |
| `teacher-web/e2e/teacher.spec.ts` | 8938 | inventariado; revisión funcional no demostrada |
| `teacher-web/index.html` | 311 | inventariado; revisión funcional no demostrada |
| `teacher-web/nginx.conf` | 506 | inventariado; revisión funcional no demostrada |
| `teacher-web/package-lock.json` | 74304 | JSON válido; no certifica contrato |
| `teacher-web/package.json` | 908 | JSON válido; no certifica contrato |
| `teacher-web/playwright.config.ts` | 380 | inventariado; revisión funcional no demostrada |
| `teacher-web/README.md` | 1663 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/app/App.tsx` | 4898 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/app/AuthContext.tsx` | 1678 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/components/FlagCard.tsx` | 3867 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/components/Icon.tsx` | 1577 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/components/QuestionsEditor.tsx` | 3243 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/components/ui.tsx` | 754 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/hooks/useAsync.ts` | 1042 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/main.tsx` | 350 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/pages/Admin.tsx` | 4021 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/pages/Alerts.tsx` | 1262 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/pages/Assignments.tsx` | 10101 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/pages/Classrooms.tsx` | 4393 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/pages/Dashboard.tsx` | 8352 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/pages/Login.tsx` | 3462 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/pages/Planning.tsx` | 8186 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/pages/Students.tsx` | 9464 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/services/api.ts` | 4978 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/styles.css` | 20683 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/test/api.test.ts` | 4895 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/test/components.test.tsx` | 7497 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/test/integration.test.ts` | 1652 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/test/setup.ts` | 43 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/test/useAsync.test.tsx` | 795 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/types/api.ts` | 4975 | inventariado; revisión funcional no demostrada |
| `teacher-web/src/utils/format.ts` | 657 | inventariado; revisión funcional no demostrada |
| `teacher-web/tsconfig.e2e.json` | 89 | JSON válido; no certifica contrato |
| `teacher-web/tsconfig.json` | 496 | JSON válido; no certifica contrato |
| `teacher-web/vite.config.ts` | 394 | inventariado; revisión funcional no demostrada |
| `tests/README.md` | 193 | inventariado; revisión funcional no demostrada |
