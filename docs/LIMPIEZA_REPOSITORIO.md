# Limpieza del repositorio

Fecha: 2026-10-26. **Archivos eliminados: ninguno.**

## Decisiones y recuperación

La carpeta recibida no tenía `.git`; no existía evidencia de archivos versionados
ni historial recuperable. Se inicializó Git en `audit/modernizacion-kawsay`.
Se conservaron las bases, archivos WAL/SHM, modelos y recursos. Los informes
generados existentes se regeneraron únicamente mediante sus generadores.

| Ruta / grupo | Procedencia y necesidad | Referencias / regeneración | Decisión |
|---|---|---|---|
| `__pycache__/`, `*.pyc` | Bytecode CPython | Regenerable al importar; no se comprobó individualmente cada caché | Ignorados; conservados hasta limpieza recuperable |
| `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` (raíz y backend) | Cachés de pruebas/análisis | Herramientas instaladas los regeneran; podrían conservar evidencia de sesiones anteriores | Ignorados; no borrados |
| `.venv/` | Entorno Python usado efectivamente por pytest y herramientas | Regenerable desde requisitos; hay herramientas locales adicionales | Conservado para verificaciones |
| `teacher-web/node_modules/` | Dependencias npm | `npm ci` y package-lock; usadas por build/E2E | Conservado e ignorado |
| `teacher-web/dist/` | Compilación web | `npm run build`; Docker construye desde fuentes | Regenerado por build, ignorado |
| `teacher-web/test-results/` | Capturas Playwright y resultados | `npm run test:e2e`; evidencia útil | Conservado e ignorado |
| `.kawsay-e2e-*/browser.db*` | Directorios con nombres del harness E2E | El harness usa DB DEMO temporal; no se inspeccionó contenido de directorios históricos ni estado de handles | No eliminar ni separar DB/WAL/SHM sin verificar y respaldar |
| `backend/data/kawsay.db*` | Persistencia del servidor, contenido potencialmente sensible | No regenerable de forma equivalente sin copia consistente | Protegido; no leído ni modificado intencionadamente |
| `backend/.env` | Configuración privada | Se verificó la exclusión en Git, no su contenido | Protegido; nunca mostrado ni añadido |
| `ml/models/`, `ml/reports/`, `ml/registry/` | Artefactos experimentales y trazabilidad | Modelos referenciados por registro; conservar histórico | Preservados; nuevo candidato añadido |
| `mobile/`, `docs/19-decisions/` | Código y decisiones existentes | Referencias activas o documentación de arquitectura | Conservados |

`.gitignore` amplía la protección a `venv/`, `env/`, bases SQLite adicionales,
WAL/SHM, logs, cobertura, artefactos Flutter, configuración Android local y
keystores. Se eliminó una línea duplicada de `.venv/` en el propio ignore.

## Criterio antes de un borrado posterior

Comprobar productor, importaciones/referencias, procesos activos, Git, valor de
evidencia, posibilidad de regeneración y copia recuperable. No hay aprobación de
borrados dudosos en esta entrega. Para retirar directorios E2E históricos o
instalaciones completas, preparar una copia y confirmar su alcance con el autor.
Nunca usar una copia simple del `.db` mientras exista WAL activo como respaldo:
usar el mecanismo SQLite backup del proyecto.

Inventario reproducible: `python scripts/audit_inventory.py`. Omite secretos,
dependencias y generados; calcula hashes de texto sin publicar su contenido.
Los hashes no se usan como justificación suficiente para borrar archivos.
