# Estado observado — 30 de octubre de 2026

Fuente: ZIP del 26/10 recibido del usuario, conservado como commit base `1ffb149`. Trabajo en rama `codex/respaldo-20261030`. No se usó la carpeta de OpenCode como fuente de cambios ni se hizo push o despliegue.

## Resultado de la fase

Reconocimiento y línea base completados. Se corrigió la revocación de sesiones y se añadió un recorrido web offline con almacenamiento cifrado. El criterio de diez respuestas, cierre completo y reapertura de Chromium, reconexión y persistencia sin duplicados fue ejecutado contra FastAPI real. La creación y publicación docente de esa actividad se preparan por API; la resolución del estudiante y la consulta del resumen docente pasan por interfaces reales.

| Verificación | Respaldo antes de cambios | Versión entregada |
|---|---:|---:|
| Backend pytest | 141 aprobadas | 143 aprobadas |
| ML pytest | 17 aprobadas | 17 aprobadas; código ML intacto |
| React/Vitest | 20 aprobadas | 28 aprobadas |
| Integración web HTTP | — | 1 aprobada |
| Playwright Chromium | — | 10 aprobadas |
| Offline producción / reinicio completo | no existía | 1 aprobada |
| TypeScript y compilación web | correctos | correctos |
| Flutter | 11 aprobadas | 11 aprobadas |
| Flutter analyze | 8 avisos informativos | sin incidencias; 3 deprecaciones se suprimen puntualmente para conservar compatibilidad con Flutter 3.22 |
| APK / Android físico | no comprobado aquí | pendiente; sin APK nuevo |

Los comandos, incidencias y pruebas no ejecutadas están en [REPORTE_PRUEBAS.md](REPORTE_PRUEBAS.md). La matriz evita considerar completa una función solo por existir su código.

## Archivos y comportamiento cambiado

- `backend/app/core/security.py`, `permissions.py`, `backend/app/modules/auth/service.py`: los access tokens incorporan `sid`, enlazado a la familia de refresh tokens vigente. Logout, reutilización de refresh y restablecimiento de PIN revocan también el acceso inmediato. Pruebas en `backend/tests/test_auth.py`.
- `teacher-web/src/services/offlineVault.ts`: almacén nuevo en IndexedDB; identidad, actividades, estados y respuestas se guardan cifrados. La frase y la clave derivada no se persisten. Escrituras entre pestañas protegidas por Web Locks y revisión transaccional.
- `teacher-web/src/services/offlineLearning.ts`: descarga por páginas del contrato existente y sincronización por lotes; confirma cada UUID y conserva rechazos e interrupciones.
- `OfflinePanel.tsx`, `OfflineActivity.tsx`, `AuthContext.tsx`, `Login.tsx`, `App.tsx`, `StudentHome.tsx`, `StudentActivity.tsx`: preparación, acceso local, recuperación, envío autenticado y borrado local únicamente sin respuestas pendientes. Se conserva el diseño y el recorrido en línea anterior.
- `pendingAttempts.ts`: comprobación de respuestas de la cola anterior antes de salir o preparar la descarga; no se borra ni migra silenciosamente esa cola.
- `teacher-web/scripts/offline-shell.mjs`, `vite.config.ts`, `src/main.tsx`: caché del shell y recursos de producción, sin almacenar respuestas API.
- `scripts/browser_e2e.py`: servidor aislado para producción offline, base temporal y cierre acotado de procesos en Windows sin depender de inspección de árboles de procesos.
- `teacher-web/src/test/offlineLearning.test.ts`, `e2e/vault.spec.ts`, `offline-e2e/learning.spec.ts` y configuraciones: fallos, concurrencia, cifrado y prueba integral. Se añadió únicamente `@types/node` como dependencia de desarrollo y se actualizó el lockfile.
- Flutter: `rules.dart`, `activity_screen.dart`, `settings_screen.dart`: controles de ciclo de vida tras esperas y protección del botón durante el guardado; se conserva SQLite y su esquema.

## Límites y siguiente fase

Esta entrega verifica el nuevo recorrido **web**. SQLite móvil sigue sin cifrado; su desbloqueo local seguro y migración conservando colas requieren una fase propia. La cola web anterior sigue sin cifrado y solo debe usarse con datos de prueba. No se probó Android físico ni se generó una plataforma Android nueva desde este respaldo.

También quedan pendientes Mis cursos integrado en ambos clientes, evaluaciones pedagógicas de entrada/salida, adaptación 1–6 curricular, aislamiento administrativo completo, validación curricular y lingüística, y ejecución real de n8n. El ML sigue siendo experimental; no se entrenó con datos reales.

La siguiente fase debe ampliar la protección móvil y completar el ciclo educativo de entrada → actividades → salida → docente, con pruebas de interfaz y revisiones curriculares documentadas. Detalle en [PENDIENTES_HACKATON.md](PENDIENTES_HACKATON.md).
