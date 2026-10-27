# ADR-003 · PostgreSQL como fuente de verdad
**Estado:** REEMPLAZADO por ADR-010 (SQLite)
## Contexto
Integridad referencial, restricciones CHECK, JSONB para evidencias, analítica por ventanas.
## Decisión
PostgreSQL central; SQLite **no** se usa como base central.
## Alternativas
MySQL; MongoDB (integridad más débil para este dominio); SQLite central (concurrencia limitada).
## Consecuencias
+ Integridad, índices, particionado futuro de `learning_attempts`; − operación y backups a cargo del equipo.
