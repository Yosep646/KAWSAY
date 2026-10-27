# ADR-010 · SQLite como base de datos del servidor
**Estado:** Aceptado (decisión del autor, Yosep). **Reemplaza a ADR-003 (PostgreSQL).**
## Contexto
El proyecto debe poder descomprimirse y ejecutarse en VS Code sin instalar ni administrar un servidor de base de datos, y la app móvil ya usa SQLite.
## Decisión
SQLite (archivo) con WAL, `foreign_keys=ON`, `BEGIN IMMEDIATE`, migraciones Alembic en modo batch, fechas UTC, secuencias por tabla `counters`,
y triggers para la evidencia append-only.
## Alternativas
PostgreSQL (mejor concurrencia y escalado; requiere servidor); MySQL; SQLite en memoria (no persiste).
## Consecuencias
+ Cero instalación, respaldo = copiar un archivo (`python scripts/dev.py backup`), pruebas rápidas y aisladas (una copia de la base por prueba).
− Un solo escritor: no escalar a varias réplicas; las llamadas lentas no pueden retener transacciones; cifrado en reposo no incluido (usar cifrado de disco).
− Si el piloto crece, hay que planificar la migración a PostgreSQL (los modelos son portables; ver `06-database-design.md`).
