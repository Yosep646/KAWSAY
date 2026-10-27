# ADR-005 · React + TypeScript (strict) para el panel docente
**Estado:** Propuesto
## Contexto
Panel web responsive con formularios complejos (revisión/edición de variantes) y dashboards.
## Decisión
React + TypeScript estricto, estructura por features, cliente API tipado generado desde OpenAPI.
## Alternativas
Flutter Web (reutiliza código pero peor para formularios/SEO/peso); Vue; server-rendered.
## Consecuencias
+ Ecosistema amplio, tipos compartidos con el contrato OpenAPI; − segundo stack de frontend.
