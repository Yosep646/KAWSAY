# KAWSAY AI — implementación incremental y evidencia de pruebas

## Cambios de esta entrega
- `teacher-web/src/pages/StudentActivity.tsx`: cargar primero la actividad descargada en IndexedDB; cuando la API no responde, permitir visualizar y responder a la actividad almacenada. Las respuestas se escriben en una cola local antes de intentar enviarlas. Reintento manual y al recuperar conectividad, únicamente para la actividad abierta. Una respuesta no confirmada impide avanzar a la siguiente pregunta.
- `teacher-web/public/sw.js`: Service Worker para recursos estáticos e interfaz de la aplicación, sin cachear solicitudes API.
- `teacher-web/src/main.tsx`: registra el Service Worker únicamente en build de producción.
- Se conservan los tres paneles y estilos administrativos, docentes y estudiantiles de la entrega anterior.

## Evidencia de pruebas ejecutadas
- `python -m pytest ml/tests -q`: **17 pasadas**.
- `python -m pytest backend/tests/test_assignments.py backend/tests/test_auth.py -q`: **26 pasadas**.
- `python -m pytest backend/tests/test_sync_reto10.py -q`: **11 pasadas**.
- `node --check teacher-web/public/sw.js`: **aprobado**.
- `npm run build`: **NO COMPLETADO**. Las dependencias JavaScript montadas eran directorios vacíos (`vite/client`, `vitest/globals`, `@testing-library/jest-dom` no disponibles). `npm ci` no terminó dentro del tiempo disponible y el entorno Node 22.16.0 está por debajo del requerido por varias dependencias. Repetir con Node compatible y acceso al registry.

## Límites que todavía deben resolverse
- La recarga offline tras cerrar sesión o sin sesión válida no está garantizada porque la autenticación sigue requiriendo verificación online.
- La cola local admite solamente una respuesta pendiente por actividad; no es una sincronización offline completa con múltiples ejercicios simultáneos.
- El Service Worker exige pruebas en HTTPS y navegador real; no se realizaron.
- Los tres paneles necesitan pruebas visuales y de extremo a extremo en navegador; estas modificaciones no equivalen a los mockups completos.
- Se probaron componentes backend de asignaciones y autenticación, no toda la suite ni un despliegue Render.
- Los modelos ML incluidos en el repositorio se encuentran marcados como experimentales basados en datos sintéticos; faltan datos reales autorizados para entrenamiento/validación educativa. Las pruebas aprobadas no constituyen validación sobre alumnos.

## Siguiente verificación local
En `teacher-web`, con una versión de Node compatible y conectividad al registro npm: `npm ci && npm run build && npm test`. Ejecutar luego pruebas de navegación y reconexión sobre HTTPS.
