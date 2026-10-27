# 05 · Arquitectura

## Estilo
**Monolito modular** (FastAPI) + clientes. Sin microservicios hasta que haya necesidad medida.

```
App Estudiante (Flutter)  ──┐
   SQLite + Sync Engine     ├── HTTPS /api/v1 ──► FastAPI
Panel Docente (React/TS)  ──┘                      ├ auth
                                                   ├ education (curriculum, activities, assignments)
                                                   ├ learning + adaptive engine (reglas)
                                                   ├ analytics (progreso, flags, recomendaciones)
                                                   ├ sync
                                                   └ ai_gateway ──► proveedor A | B | local
                                                   SQLite (archivo, WAL) ── respaldos
```

## Reglas de dependencia
- `route → service → repository → DB`. Reglas pedagógicas en `service`/`domain`, nunca en rutas.
- Módulos se comunican por interfaces de servicio, no por tablas ajenas.
- `ai_gateway` es un puerto (`AIProvider`) con adaptadores; el dominio no importa SDKs de proveedores.
- Flutter: `presentation / domain / data`; Riverpod o Bloc (decisión en Fase 7). Sin lógica en widgets.
- React: `pages / components / features / services / hooks / types / utils`, TypeScript `strict`.

## Motor adaptativo y analítica
Paquete de dominio puro (sin I/O) con reglas versionadas en configuración. Se ejecuta en el backend al recibir intentos (síncrono en MVP; cola/worker cuando haya carga) y una **versión ligera de reglas** corre en el cliente para pistas/dificultad offline.

## Flujo de automatización (en backend, sin n8n)
intento recibido → validación/idempotencia → persistir → recalcular progreso de competencia → evaluar reglas → (support_flag) → recomendación → visible al docente.

## Repositorio
```
KAWSAY-AI/
├── backend/{app/{core,modules/*,shared,workers},migrations,tests,Dockerfile,requirements.txt}
├── mobile/{lib/{app,core,features,shared},assets,test}
├── teacher-web/{src/{app,pages,components,features,services,hooks,types,utils},Dockerfile}
├── ai/{gateway,tutor,adaptation,analytics,recommendations,motivation,languages,safety}
├── database/   (seeds de ejemplo no reales, scripts)
├── infrastructure/
├── docs/
├── tests/      (E2E: offline, multigrado, adaptativo)
├── docker-compose.yml  .env.example  .gitignore  README.md
```
Nota: `ai/` se empaqueta como librería Python importada por el backend (no servicio aparte) hasta que se necesite escalar.

## Docker (Fase 1)
`backend` + `teacher-web` (+ `dispatcher` opcional). La base es un archivo SQLite en un volumen. Redis y almacenamiento de objetos: no se usan.
