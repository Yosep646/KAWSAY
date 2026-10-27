# Auditoría de paneles web

## Línea base

La aplicación existente está en `teacher-web/`: React 18, TypeScript, Vite y React Router. `src/app/App.tsx` contiene rutas protegidas y navegación; `src/app/AuthContext.tsx` gestiona la sesión y `src/services/api.ts` concentra HTTP, refresh, tiempo de espera y errores. El backend usa roles `ADMIN`, `TEACHER` y `STUDENT`, y verifica permisos en sus rutas. La rama existente `audit/modernizacion-kawsay` no tiene commits y el proyecto aparece sin seguimiento.

| Área | Evidencia y situación |
|---|---|
| Docente | `Dashboard`, `Classrooms`, `Students`, `Planning`, `Assignments` y `Alerts` consumen la API. Los flujos cubiertos por pruebas previas no acreditan todas las pantallas solicitadas. |
| Administrador | `Admin.tsx` consulta escuelas, auditoría y automatización, crea escuelas/docentes e importa currículo. No dispone de dashboard completo, mapa, reportes ni CRUD integral. |
| Estudiante | El frontend anterior rechazaba el rol. Se añadió acceso con código/PIN y vista inicial conectada a `/sync/pull` y `/progress/me`, protegida por rol. Vista solo en línea: no resuelve ni guarda ejercicios. |
| Seguridad | Las rutas web son barreras de navegación; la autorización real se mantiene en FastAPI. La sesión web usa refresh en sessionStorage; la protección y recuperación offline de menores aún no están implementadas. |
| Diseño | Estilos y componentes compartidos existentes; se añadieron acentos por rol. No se ha reproducido toda la referencia ni verificado WCAG integral. |
| Offline | No existe service worker, IndexedDB ni cola de respuestas web. No se presenta la vista web como offline. Flutter también requiere validación en dispositivo. |
| Datos y ML | No se han añadido métricas ficticias; el ML sigue experimental con datos sintéticos. |

La auditoría inicial incluyó rutas, contexto de autenticación, cliente HTTP, estilos, panel administrativo, endpoints de autenticación y aprendizaje, `package.json` y pruebas unitarias existentes. `npm test -- --run`: 18 aprobadas; excluye la prueba HTTP de integración. La revisión semántica de todos los archivos y la implementación completa de los tres paneles siguen pendientes.

## Verificación posterior

- `npm run build`: TypeScript y Vite correctos. `npm test -- --run`: 19 aprobadas, incluida una prueba de acceso de estudiante con respuestas HTTP simuladas.
- `npm run test:e2e`: 1 prueba HTTP real y 5 pruebas Chromium del panel docente aprobadas. El escenario del script para conectividad offline usa una cola simulada; no demuestra una PWA offline. La nueva vista de estudiante no se probó en navegador contra el backend real.
- No se eliminaron archivos ni se incorporaron dependencias. Falta implementar resolución de actividades, persistencia y sincronización offline web, panel administrativo integral y las demás pantallas descritas en el requerimiento.

## Corrección de listado de estudiante

La primera implementación pedía `limit=100`, pero `/sync/pull` admite como máximo 50 y respondía 422. Se cambió a páginas de 50 con carga explícita de páginas siguientes y validación del cursor. `npm run build` pasó y `npm test -- --run` terminó con 20 pruebas aprobadas, incluida la paginación con HTTP simulado. Falta probar esta vista contra el backend real y completar la resolución, recuperación y sincronización de respuestas.

## Actividades en línea

Se añadió apertura de actividades, preguntas de selección múltiple, numéricas y texto, envío mediante `/sync/push` y consulta de estado propio mediante `/sync/tasks/{id}/attempts`. No es una PWA offline ni una entrega final completa. La consulta de estado se probó contra FastAPI con control de acceso; la nueva interfaz no se ha validado extremo a extremo contra el backend real. `pytest backend/tests/test_sync_reto10.py -q`: 11 aprobadas; `npm test -- --run`: 20 aprobadas; `npm run build`: correcto.

### Cola web parcial posterior

El evento pendiente se guarda ahora en IndexedDB antes del envío y se elimina tras ACK o DUPLICATE y actualización del estado. Se separa por ID de usuario y actividad; el mismo UUID se conserva al reintentar. Prueba Chromium comprobó persistencia tras recarga. **Limitaciones críticas**: IndexedDB no está cifrado y el aislamiento por clave no protege frente a otra persona con acceso al mismo navegador; no usar con datos sensibles de menores en dispositivos compartidos. No hay service worker ni apertura de actividades sin conexión, reintento automático, borradores, resolución de conflictos ni prueba integral de corte/reconexión. El navegador puede eliminar el almacenamiento. La prueba de IndexedDB no demuestra sincronización offline completa.

Una confirmación anterior ahora solo elimina la entrada si coincide el UUID del evento actualmente almacenado; una confirmación tardía de otra pestaña no puede borrar una respuesta nueva. Se comprobó en Chromium; `npm run test:e2e`: 7 pruebas de navegador y 1 integración HTTP aprobadas. `npm test -- --run`: 20 aprobadas; `npm run build`: correcto. Flutter sigue sin iniciar tras un nuevo intento de 60 segundos.
