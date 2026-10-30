# KAWSAY AI

**Autor: Yosep** · Plataforma educativa adaptativa, offline-first y multigrado para aulas rurales.
Foco del hackathon: **Reto 10 — tecnología que encuentre a quien estamos dejando atrás**: detectar, con evidencia explicable, qué estudiantes
necesitan apoyo y en qué competencia, también donde Internet no siempre llega. KAWSAY **no reemplaza al docente**: el currículo define qué se
aprende, el docente decide qué publicar, y KAWSAY adapta cómo.

> **Cómo ejecutarlo en VS Code: `docs/GUIA_VSCODE.md`**. Base de datos: **SQLite** (sin instalar nada). Para trabajos que deban conservarse, usa `python scripts/dev.py db`, `python scripts/dev.py run` y `python scripts/dev.py web`; no reinicies los datos DEMO. Consulta **`docs/GUIA_PERSISTENCIA_SQLITE.md`**.
> **Estado real y límites de cada componente: `docs/00-repository-audit.md`.** Nada se da por funcionando sin una verificación ejecutada.

## Qué contiene
| Carpeta | Contenido | Estado |
|---|---|---|
| `backend/` | FastAPI + SQLite + Alembic: auth/RBAC, aulas multigrado, planificación curricular versionada, asignaciones con revisión docente, sync idempotente, progreso, alertas explicables, AI Gateway, tutor, idiomas, auditoría, eventos, pronóstico ML opcional | verificado (130 pruebas) |
| `teacher-web/` | Panel docente React + TypeScript estricto | diseño adaptable, verificado (tsc, 13 pruebas, build, integración real y 5 E2E en Chromium); cobertura en `docs/16-testing.md` |
| `ml/` | Entrenamiento (validación cruzada por estudiante, calibración, IC, robustez), registro, inferencia, exportador seudonimizado | verificado (9 pruebas); modelo **experimental** (sintético) |
| `mobile/` | App del estudiante Flutter (SQLite, sync, offline) | 11 pruebas locales aprobadas; **Android y dispositivo no verificados** |
| `automation/` | Workflow n8n + eventos firmados | n8n sin verificar |
| `scripts/` | `dev.py` (setup/demo/web/test/backup), `demo_e2e.py`, generadores de documentación y vectores | verificado |
| `docs/` | visión, requisitos, arquitectura, base de datos, ER y API (generados), offline/sync, IA, ML + ficha del modelo, seguridad, pruebas, despliegue, ADRs | actualizado |

## Principios que el código hace cumplir
- La IA es opcional y **nunca publica**: lo generado entra como `AI_GENERATED` y exige revisión y aprobación docente (servicio + restricción en la base).
- Las alertas muestran **evidencia**, no etiquetas ni diagnósticos; sin evidencia suficiente no hay porcentaje ni alerta.
- Privacidad de menores: datos mínimos, accesos auditados, idioma elegido por la persona (nunca inferido), solo traducciones verificadas.
- Si falla la IA, n8n o el ML, el núcleo (login, tareas, sync, progreso, alertas) sigue funcionando.
- Seguridad (ver `docs/14-security.md`): Argon2id, rotación de refresh tokens, bloqueo y rate limit, RBAC con propiedad (404 en lo ajeno), política de
  contraseñas, cabeceras de seguridad, CORS estricto, auditoría, HMAC en webhooks, `bandit`/`pip-audit`/`npm audit` sin hallazgos.

## Comandos
```bash
python scripts/dev.py setup     # instala y migra
python scripts/dev.py demo      # datos DEMO + backend en :8000
python scripts/dev.py web       # panel docente en :5173
python scripts/dev.py test      # backend, ML y unitarias del panel
python scripts/dev.py backup    # respaldo de la base SQLite
python scripts/dev.py db        # aplica migraciones y muestra ruta/estado de la base
```

E2E en Chromium (instalación y ejecución): `docs/16-testing.md`; comando desde la raíz: `npm --prefix teacher-web run test:e2e`.

## Lo que NO está terminado (dicho con claridad)
- La app Flutter no se ha compilado para Android ni probado en un dispositivo; el funcionamiento offline real del celular **no está demostrado**.
- El modelo de ML se entrenó con datos **sintéticos**; no hay datos reales ni modelo aprobado. La mejora sobre una heurística simple no es significativa.
- No hay currículo oficial cargado (solo datos DEMO), ni proveedor de IA real probado, ni n8n/Docker ejecutados, ni revisión legal de datos de menores.
- SQLite admite un solo escritor: válido para un piloto en un servidor; ver `docs/06-database-design.md` para los límites.

Licencia: por definir por el autor (Yosep).
