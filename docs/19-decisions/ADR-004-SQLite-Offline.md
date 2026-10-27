# ADR-004 · SQLite cifrado en el dispositivo
**Estado:** Propuesto
## Contexto
Funcionamiento sin red, datos de menores, dispositivos compartidos o perdibles.
## Decisión
SQLite local (con cifrado, p. ej. SQLCipher), migraciones versionadas, cola `sync_queue` transaccional.
## Alternativas
Hive/Isar/ObjectBox (NoSQL, menos relacional); archivos JSON (frágil ante cortes).
## Consecuencias
+ Transacciones ACID locales, SQL conocido; − gestionar migraciones locales y cifrado.
