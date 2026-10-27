# ADR-006 · AI Gateway desacoplado
**Estado:** Propuesto
## Contexto
Claves no deben salir de la infraestructura; proveedores cambian; contenido para menores requiere validación.
## Decisión
Puerto `AIProvider` con adaptadores intercambiables, `OutputValidator`, trazabilidad y circuit breaker. Los clientes solo hablan con el backend.
## Alternativas
SDK del proveedor llamado desde cada servicio; llamadas desde el cliente.
## Consecuencias
+ Cambio de proveedor sin tocar el dominio, resiliencia, auditoría; − una capa más que mantener.
