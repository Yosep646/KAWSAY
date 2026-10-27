# ADR-002 · FastAPI como backend
**Estado:** Propuesto
## Contexto
API REST versionada, validación fuerte, ecosistema IA/ML en Python.
## Decisión
FastAPI + Pydantic + SQLAlchemy 2 + Alembic, monolito modular.
## Alternativas
Django/DRF (admin y baterías incluidas, más pesado/acoplado); NestJS (separa lenguaje del ecosistema IA); Go (rendimiento, menos afín a IA).
## Consecuencias
+ OpenAPI automático, tipado, integración natural con IA; − hay que construir manualmente admin, permisos y disciplina de capas.
