# IA en KAWSAY — qué es real y qué no

**Hoy NO hay ningún proveedor de IA conectado.** `AI_PROVIDER=disabled` por defecto. Todo lo demás funciona sin IA.

Real y probado: `AIGateway` (puerto `AIProvider`, reintentos acotados, circuit breaker), `ContextBuilder` (solo grado, área, competencia,
tema, objetivo y texto del docente entre `<docente>…</docente>`; **sin datos de estudiantes**), `OutputValidator` (JSON/esquema, sin URLs,
correos ni teléfonos, contenido inapropiado, complejidad por grado), `CurriculumValidator` (área, competencia, tema y grado declarados deben
coincidir; términos del tema presentes; sin mencionar otras áreas → `NEEDS_REVIEW`), trazabilidad en `ai_generation_requests` (sin contenido).
Todo contenido generado entra como `AI_GENERATED`: **no se aprueba ni se publica sin revisión y aprobación docente** (servicio + CHECK en BD).
Un `NEEDS_REVIEW` exige confirmar las advertencias para aprobar. Si la IA cae: 503 claro y variantes manuales; el resto sigue.
Tutor: pistas de reglas/docente; la IA solo reformula y se descarta si filtra la respuesta; no recibe la respuesta correcta ni texto libre.

Sin verificar: el adaptador `AnthropicProvider` contra el servicio real. Para activarlo: `AI_PROVIDER=anthropic`, `AI_MODEL`, `AI_API_KEY` (solo servidor).
Las pruebas usan `tests/fakes.py` (proveedores falsos exclusivos de pruebas). No se afirma calidad pedagógica de lo que genere un modelo real:
hay que evaluarla con docentes antes de usarla.
