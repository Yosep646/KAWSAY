# 00 · Análisis de requisitos: contradicciones, riesgos y decisiones pendientes

Estado: **PROPUESTA – requiere aprobación**

## A. Tensiones / contradicciones detectadas

| # | Tensión | Resolución propuesta |
|---|---------|----------------------|
| C1 | "Offline-first" vs. "Tutor KAWSAY conversacional" (requiere LLM). | Tutor offline = **tutor guiado por reglas** con pistas/explicaciones pregeneradas y aprobadas. Conversación libre solo online. Se documenta como límite explícito. |
| C2 | "IA no simulada / sin datos falsos" vs. fases 1-5 sin proveedor IA. | La IA es **opcional**. Hasta la Fase 6 el docente crea variantes manualmente. Los mocks de IA existen **solo en tests**; en desarrollo se usa proveedor real o el flag `AI_PROVIDER=disabled`. |
| C3 | MVP exige "sincronizar y analizar" (Fases 9-12) pero "Quiero aprender" está en la Fase 10. | Se propone reordenar: primero el corte vertical docente→publicar→offline→sync→dashboard; después "Quiero aprender" (ver `18-roadmap.md`). |
| C4 | Panel docente web "online" vs. docentes rurales con conectividad limitada. | MVP: web online con **borradores locales** (IndexedDB) y reintento. PWA/offline docente = post-MVP. Riesgo declarado. |
| C5 | Login de menores: el prompt no define cómo se crean cuentas (¿email? ¿auto-registro?). | Cuentas de estudiante **provisionadas por el docente** (código + PIN), sin email obligatorio. Sesión ligada a dispositivo. |
| C6 | Access token de corta duración vs. uso offline prolongado. | El acceso offline a datos locales **no depende del token**: depende de un desbloqueo local (PIN/perfil). El token solo se exige para sincronizar. Refresh token con vida larga y rotación; revocación por dispositivo. |
| C7 | Progreso "recalculable desde eventos" vs. progreso local en SQLite. | El progreso local es **provisional/visual**. El servidor es la autoridad y lo recalcula desde `learning_attempts`; el pull devuelve el valor oficial. |
| C8 | Diagrama incluye Object Storage, pero Docker fase inicial no. | Almacenamiento en disco local (volumen) tras interfaz `StorageBackend`; S3/MinIO cuando haya Learning Packs reales (Fase 8). |
| C9 | `performance_expectations` por grado vs. currículo organizado por ciclos. | Ver riesgo R1. |

## B. Riesgos

**R1 – Currículo (alto).** Si se usa el Currículo Nacional peruano (CNEB), los estándares de aprendizaje se organizan por *ciclo* (varios grados), no por grado. El modelo debe permitir `competency` → `capacity` → `performance_expectation` con vínculo a **grado y/o ciclo**. Además: no hardcodear el currículo; importarlo desde fuente oficial **verificando licencia/uso**. *Acción: confirmar país/currículo objetivo del piloto.*

**R2 – Privacidad de menores (alto).** Requiere base legal, consentimiento del tutor/escuela, política de retención y minimización. En Perú aplica la normativa de protección de datos personales (Ley 29733 y reglamento): **validar con asesoría legal** antes del piloto. El sistema NO guarda GPS, solo ubicación administrativa (región/comunidad opcional).

**R3 – Contenido lingüístico (alto).** Variantes de quechua/aimara difieren entre regiones. Sin revisión de especialistas, no se publican traducciones. Modelo: `content_translation.status ∈ {draft, in_review, verified, rejected}` y solo `verified` se entrega al estudiante.

**R4 – Seguridad del contenido generado para niños (alto).** `OutputValidator` obligatorio (longitud, vocabulario, temas prohibidos, esquema) + aprobación docente; nunca publicación automática.

**R5 – Datos locales en dispositivos compartidos/perdidos (medio).** SQLite cifrado (SQLCipher o equivalente), multi-perfil por dispositivo, borrado remoto lógico (revocación de dispositivo).

**R6 – Metodología de progreso sin definir (medio).** Propuesta inicial en `12-adaptive-learning.md` (media móvil ponderada por competencia, con mínimo de evidencia). Debe validarse con docentes/pedagogos. Se muestra "sin evidencia suficiente" en vez de un % si hay pocos intentos.

**R7 – Relojes de dispositivos poco fiables (medio).** No se confía en `client_created_at` para ordenar; se usa `(device_id, client_seq)` + `received_at` del servidor.

**R8 – Alcance (alto).** 16 fases es muy ambicioso. Se recomienda cerrar el corte vertical del MVP antes de abrir "Tutor" y "Lenguas". Capacidad del equipo no especificada.

**R9 – Peso de Learning Packs (medio).** Audio/imagen en zonas de bajo ancho de banda: paquetes por grado+materia, compresión, descargas reanudables y actualizaciones diferenciales.

**R10 – Sesgo/justicia en alertas (medio).** Las alertas son reglas auditables con evidencia visible; no usan atributos sensibles (lengua, comunidad) como entrada del detector.

## C. Decisiones que necesito de ti (ver también el mensaje final)
1. País/currículo del piloto y fuente oficial.
2. Cuentas de estudiante provisionadas por docente (C5): ¿ok?
3. Panel docente: ¿online en MVP (C4)?
4. Reordenar fases (C3): ¿ok?
5. Proveedor IA para pruebas reales (o dejar `disabled` hasta Fase 6).
