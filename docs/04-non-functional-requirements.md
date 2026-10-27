# 04 · Requisitos no funcionales

| ID | Categoría | Requisito | Medición |
|----|-----------|-----------|----------|
| RNF-01 | Offline | Tarea descargada se completa 100 % sin red | Test E2E offline |
| RNF-02 | Sync | Idempotente: reenvío N veces = 1 registro | Test sync |
| RNF-03 | Datos | Cero pérdida de intentos tras cierre/crash de app | Test de persistencia |
| RNF-04 | Rendimiento | API p95 < 500 ms (endpoints no-IA) con 500 usuarios concurrentes | Prueba de carga |
| RNF-05 | Bajo ancho de banda | Sync de un día típico < 200 KB; packs con descarga reanudable | Medición |
| RNF-06 | Dispositivos | Android 8+ (API 26+), 2 GB RAM | Pruebas en gama baja |
| RNF-07 | Seguridad | Hash Argon2id/bcrypt, JWT corto, RBAC en backend, rate limit, CORS restringido | Tests de seguridad |
| RNF-08 | Privacidad | Minimización, sin GPS, auditoría, cifrado en tránsito y SQLite cifrado | Revisión |
| RNF-09 | Resiliencia IA | Caída del proveedor no afecta login, offline ni reglas adaptativas | Test con gateway caído |
| RNF-10 | Observabilidad | Logs estructurados, request-id, /health y /ready, métricas básicas, sin secretos en logs | Revisión |
| RNF-11 | Accesibilidad | Botones ≥ 48 dp, contraste WCAG AA, pocos elementos por pantalla, audio opcional | Auditoría UX |
| RNF-12 | Mantenibilidad | Monolito modular, capas route→service→repository, cobertura mínima backend 80 % en dominio | CI |
| RNF-13 | Versionado | API `/api/v1`; esquema SQLite con migraciones; packs versionados | Revisión |
| RNF-14 | i18n | Textos externalizados; idiomas añadibles sin cambiar código | Revisión |
| RNF-15 | Portabilidad | Docker Compose reproducible | `docker compose up` |
