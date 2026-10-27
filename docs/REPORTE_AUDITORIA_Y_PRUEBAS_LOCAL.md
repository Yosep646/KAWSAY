# KAWSAY AI — Auditoría e instalación local
**Fecha:** 27 de octubre de 2026 · **Alcance:** último ZIP de código adjuntado que estaba disponible en esta conversación (`KAWSAY_AI_verificado_parcial_2026-10-27.zip`).

> Esta revisión no incluye ninguna modificación que ChatGPT Work pudiera haber hecho después en la PC del usuario, porque no se adjuntó su carpeta actualizada. No asumir que el proyecto está listo para producción.

## Cambios concretos implementados

| Archivo | Corrección |
|---|---|
| `teacher-web/nginx.conf` | Nginx reenvía `/api/` a FastAPI; `/health` y `/ready` funcionan desde la misma URL; SPA conserva rutas `/admin`, `/docente`, `/estudiante`. Encabezados antiframe, anti-MIME, privacidad y CSP; sin caché en respuestas API/HTML. |
| `teacher-web/src/pages/StudentActivity.tsx` | Corregido error TS2345 del acceso al primer elemento de la cola y añadido bloqueo síncrono de envíos simultáneos. |
| `docker-compose.yml` | Puertos de localhost seguros por defecto, `WEB_BIND_IP` para LAN opcional, volumen persistente para SQLite, nginx como punto de entrada, servicio de backend. |
| `.env.example`, `.gitignore`, `.dockerignore` | Variables documentadas; secretos, bases de datos, entornos y dependencias excluidos de Git y del contexto Docker. El JWT debe generarse aleatoriamente. |
| `scripts/run_local.sh`, `iniciar_kawsay_windows.ps1` | Inicio local con clave aleatoria, sin crear automáticamente una cuenta con contraseña pública de demostración. |
| `scripts/smoke_local_stack.py` | Verifica que las tres rutas web respondan, salud del backend, disponibilidad de BD y API protegida (requiere servidor levantado). |
| `scripts/test_offline_browser.py` | Prueba en Chromium para la cola IndexedDB por alumno, ACK, contenido cacheado y shell PWA; no se pudo ejecutar aquí por bloqueo de la navegación del navegador. |
| `scripts/demo_e2e.py` | Prohibida por defecto la creación de datos demo sin activación explícita y contraseña específica. |
| `ml/reports/kawsay-diff-20261026203213-cce4aa.json` | Codificación Windows-1252 corregida a UTF-8 sin alterar la información histórica del modelo sintético. |
| `README_DEPLOY_RAPIDO.md` | Guía completa para Windows, Linux, LAN y limitaciones de hosting gratuito. |

## Resultados ejecutados en esta sesión

- **87/87 pruebas seleccionadas aprobadas**: autenticación, actividades, sincronización, permisos, seguridad, salud y ML. Comando: `pytest -q backend/tests/test_auth.py backend/tests/test_assignments.py backend/tests/test_sync_reto10.py backend/tests/test_security_hardening.py backend/tests/test_health.py backend/tests/test_authorization_and_multigrade.py ml/tests/test_ml_pipeline.py` con `APP_ENV=test`, `PYTHONPATH=backend`, `JWT_SECRET` temporal de pruebas.
- **TypeScript `tsc --noEmit`: aprobado.** Se recuperaron dependencias de tipado desde el ZIP original para aislar los errores de código; **no se incluyen** estas dependencias en la entrega.
- **Nginx `nginx -t`: aprobado.** Prueba HTTP con backend simulado: ruta `/estudiante` devolvió HTML, ruta `/api/v1/auth/me` devolvió JSON del backend y `/health` se redirigió correctamente. Esta prueba no sustituye el `docker compose up` real.
- **Python `compileall`: aprobado** (backend, ML, scripts).
- **13 JSON validados**, incluida la normalización del reporte ML; 4 archivos YAML procesados correctamente.
- **Inventario automatizado** de archivos originales y modificados: `docs/AUDITORIA_INVENTARIO_ACTUAL.json`, con rutas, tamaños, módulos y hashes SHA-256. No equivale a una auditoría humana línea por línea.

## Verificaciones aún NO aprobadas

1. **React `vite build`**: sigue sin terminar en este entorno, por Node v22.16.0 y falta de binding nativo Linux de Rolldown/Vite y sin acceso completo al registro npm. La revisión TypeScript sí pasó. Docker con `node:24-alpine` y acceso a Internet debería poder descargar las dependencias; se debe probar en el equipo del usuario.
2. **Prueba offline real**: las 11 pruebas de sincronización backend pasan, pero el intento de abrir Chromium local dio `net::ERR_BLOCKED_BY_ADMINISTRATOR`; no se comprobó el funcionamiento de la PWA en un navegador real. El script incluido se podrá ejecutar en un equipo sin esa restricción.
3. **Reapertura de sesión sin Internet**: el frontend actual requiere refrescar la sesión con el servidor. Aunque haya actividades en IndexedDB, cerrar el navegador y volver a iniciar sesión offline **no está resuelto**. No ofrecerlo como función finalizada.
4. **Suite completa backend**: se intentó dos veces; no terminó antes del límite de ejecución. Las 87 pruebas indicadas arriba son verificaciones completas separadas, no un resultado de toda la suite.
5. **Flutter/Android**: el ZIP contiene código Dart pero no proyecto Android completo y no hay SDK Flutter disponible. No es posible afirmar compilación móvil.
6. **ML con datos reales**: los modelos del ZIP son experimentales con `data_kind=SYNTHETIC`, sin dataset real autorizado ni validación en colegios. No afirmar que hay entrenamiento real con alumnos.
7. **Seguridad de producción**: faltan pruebas de pentesting, análisis actualizado de vulnerabilidades de dependencias (`npm audit`, `pip-audit`), política de copias de seguridad y revisión de privacidad para datos de menores. El almacenamiento offline en el navegador no está cifrado y requiere evaluación para dispositivos compartidos.

## Seguridad: condiciones mínimas antes de exponer la web

- Mantén `WEB_BIND_IP=127.0.0.1` salvo que exista una razón para acceder desde una LAN confiable.
- Genera un `JWT_SECRET` aleatorio, utiliza contraseñas distintas y no distribuyas `.env`.
- **No publiques por HTTP abierto** una plataforma con información de menores. Para acceso desde teléfonos, usa HTTPS confiable, roles correctos y restricciones de firewall. Service Worker / PWA solo funciona en contextos seguros (`localhost` o HTTPS).
- Haz copias de seguridad del volumen Docker, conserva procedimientos de restauración y prueba el restablecimiento.
- SQLite es la DB del servidor, protegida por rol pero sin cifrado en reposo por defecto. Evalúa cifrado de disco y políticas de dispositivos.
- El modo offline local no garantiza acceso después del cierre de sesión, y no hay garantías de seguridad multiusuario en dispositivos compartidos hasta nuevas pruebas.
- No despliegues esta configuración con datos reales a **Render Free**: su filesystem es efímero y PostgreSQL Free expira a 30 días.

## Comandos de puesta en marcha (en la PC con Docker Desktop)

```powershell
powershell -ExecutionPolicy Bypass -File .\iniciar_kawsay_windows.ps1
python scripts/smoke_local_stack.py
# http://127.0.0.1:8080
```

Para validar React específicamente en Node >=24.15 y con Internet, dentro de `teacher-web` ejecuta: `npm ci`, `npm run typecheck`, `npm run build`, `npm test`, `npm run test:integration`, `npm run test:e2e`. Luego valida la PWA en Chrome/Edge con herramientas de red desconectada.

La entrega es **apta para instalar y continuar comprobaciones locales**, NO certificada como producción, offline integral o compilada en frontend de extremo a extremo.
