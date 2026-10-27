# ADR-008 · Monolito modular, Redis y n8n diferidos
**Estado:** Propuesto
## Contexto
Equipo reducido, MVP; automatizaciones críticas deben ser auditables.
## Decisión
Un solo servicio backend con módulos aislados; Redis/workers cuando haya cargas asíncronas reales; n8n solo para integraciones no críticas.
## Alternativas
Microservicios desde el inicio; n8n como orquestador del flujo educativo.
## Consecuencias
+ Simplicidad operativa; − requiere disciplina para mantener límites entre módulos.
