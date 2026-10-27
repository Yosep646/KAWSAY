# 14 · Seguridad (implementada y verificada)

Cada control indica la prueba que lo verifica. Estado actual: backend 130 pruebas · `bandit` sin hallazgos medios/altos ·
`pip-audit` y `npm audit` sin vulnerabilidades conocidas.

| Área | Control implementado | Verificación |
|---|---|---|
| Contraseñas | Argon2id; política NIST (12–128 caracteres, lista de comunes, sin correo/nombre); nunca en logs ni respuestas | `test_auth`, `test_security_hardening` |
| Sesiones | Access token 15 min (HS256, `iss`, `typ`, rechaza `alg=none`); refresh con **rotación y detección de reutilización** (revoca la familia); tokens guardados solo como hash | `test_auth` |
| Cambio de contraseña | exige la actual, aplica la política y **cierra todas las demás sesiones** | `test_change_password_...` |
| Desactivación | el admin desactiva una cuenta → tokens revocados al instante; no puede desactivarse a sí mismo | `test_admin_deactivates_...` |
| Fuerza bruta | bloqueo de cuenta tras 5 fallos (15 min) con mensaje idéntico, igualación de tiempos, rate limit por IP en login/refresh/IA/tutor | `test_account_lockout`, `test_rate_limit` |
| Autorización | RBAC en el servidor + propiedad: recursos ajenos → **404** (docentes, escuelas y alumnos) | `test_authorization_*`, matriz de roles |
| Inyección | ORM parametrizado; pruebas con cargas SQLi en login | `test_sql_injection_*` |
| XSS | JSON + `nosniff` + CSP `default-src 'none'`; React escapa; CSP en `nginx.conf` | `test_xss_payload_*` |
| CSRF | no aplica: autenticación por cabecera `Authorization`, sin cookies de sesión | diseño |
| CORS | lista blanca explícita (nunca `*`) | `test_cors_*` |
| Cabeceras | `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store`, HSTS en producción | `test_security_headers_*` |
| Entradas | Pydantic estricto (`extra=forbid`: sin *mass assignment*), límite de 1 MiB, `Content-Length` obligatorio (411 si es *chunked*) | `test_requests_without_verifiable_length_*` |
| Errores | sin trazas al cliente; `request_id` para soporte; docs OpenAPI desactivadas en producción | `test_unhandled_error_*` |
| Logs | JSON con redacción; intentos fallidos con huella corta del identificador, sin secretos | `test_failed_logins_are_logged_without_secrets` |
| Auditoría | `audit_log` de lecturas docentes de datos de estudiantes | `test_audit_log_*` |
| Datos | base `600` en POSIX; `learning_attempts` inmutable (triggers); respaldos con verificación de integridad | `test_database_file_is_private_...` |
| IA | claves solo en servidor; contexto sin datos de estudiantes; salida validada; nada se publica sin aprobación docente | `test_ai_gateway` |
| Webhooks | HMAC-SHA256 con marca de tiempo (anti-replay), secreto compartido | `test_support_flag_emits_...` |
| Cadena de suministro | versiones fijadas; `pip-audit`/`npm audit`/`bandit` en CI | `.github/workflows/ci.yml` |
| Secretos | `JWT_SECRET` ≥ 32 caracteres obligatorio; `.env` fuera de Git; `dev.py setup` genera uno aleatorio | `test_production_requires_strong_jwt_secret` |

## Riesgos residuales (no resueltos)
- **SQLite sin cifrado en reposo**: usa cifrado de disco (BitLocker/FileVault/LUKS) y protege los respaldos.
- Rate limit y circuit breaker **en memoria** (un solo proceso); con varios procesos habría que moverlos a un almacén compartido.
- Refresh token del panel en `sessionStorage` (una cookie `httpOnly` sería más segura).
- App móvil: SQLite local sin cifrar (pendiente SQLCipher) y sin verificar en dispositivo.
- Sin pruebas de penetración externas, sin análisis de carga, sin revisión legal de datos de menores.
- Credenciales DEMO fijas en `scripts/dev.py`: solo para uso local; no desplegar con ellas.
