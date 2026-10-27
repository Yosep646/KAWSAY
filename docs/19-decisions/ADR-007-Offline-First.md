# ADR-007 · Offline-first con sincronización por eventos idempotentes
**Estado:** Propuesto
## Contexto
Conectividad limitada; no se puede perder ni duplicar trabajo del estudiante.
## Decisión
Escritura local primero; eventos inmutables con UUID de cliente; push idempotente con ACK; pull por cursor; políticas de conflicto por entidad; progreso oficial calculado en servidor.
## Alternativas
Last-write-wins global (pierde datos); CRDT completos (complejidad excesiva); online-only con caché.
## Consecuencias
+ Robustez y auditabilidad; − más complejidad de sincronización y pruebas, progreso local solo provisional.
