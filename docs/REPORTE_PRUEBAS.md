# Pruebas ejecutadas — 30/10/2026

Entorno: Windows, Python 3.12.14, Node 24.22.1, Flutter 3.47.8 y Dart 3.13.7. Dependencias del respaldo instaladas en entorno aislado. Se usaron exclusivamente cuentas ficticias y bases temporales. No se leyó ni modificó una base de estudiantes real.

| Comando, desde su directorio | Resultado final |
|---|---|
| `backend`: `..\.venv\Scripts\python.exe -m pytest -q` | 143 aprobadas, 0 fallidas, 0 omitidas; una advertencia Starlette/httpx |
| raíz: `.venv\Scripts\python.exe -m pytest ml/tests -q` | 17 aprobadas, 0 fallidas, 0 omitidas |
| `teacher-web`: `npm run build` | TypeScript y producción correctos; incluye `sw.js` |
| `teacher-web`: `npm test` | 28 aprobadas, 0 fallidas, 0 omitidas |
| `teacher-web`: `npm run test:e2e` | integración HTTP 1 aprobada, demo API real correcta y Chromium 10 aprobadas |
| `teacher-web`: `npm run test:offline` | integración HTTP 1 aprobada y recorrido producción offline 1 aprobado; la integración es la misma y no se cuenta dos veces |
| `mobile`: `flutter pub get` | dependencias resueltas; sin actualización indiscriminada de paquetes |
| `mobile`: `flutter analyze --no-pub` | sin incidencias; tres usos de `value` se mantienen con supresión puntual para la compatibilidad mínima declarada |
| `mobile`: `flutter test --no-pub` | 11 aprobadas, 0 fallidas |
| `mobile`: `flutter devices` | no se obtuvo inventario válido: adb no pudo crear `\.android` por permisos, incluso al intentar un directorio de datos local |

## Línea base

Antes de cambios: 141 backend, 17 ML y 20 web aprobadas; build web correcto. Las primeras 11 pruebas Flutter pasaron y analyze informó ocho avisos, corregidos o documentados antes de la entrega. Estas cifras corresponden al ZIP, no a las auditorías de OpenCode.

## Cobertura nueva

- Dos pruebas backend nuevas y ampliación de logout: rotación/replay y revocación por PIN sin esperar vencimiento del access token.
- Ocho casos Vitest: confirmaciones incompletas/duplicadas/ajenas/desconocidas, aceptación parcial, interrupción después del ACK, identidad remota incorrecta y respuestas nuevas durante sincronización.
- Tres pruebas Chromium de almacén: cifrado/tamper/dueño/frase/borrado protegido, dos pestañas y renovación de acceso vencido conservando la cola.
- Un recorrido Chromium de producción: diez respuestas, red desactivada, cierre completo de proceso, nuevo proceso con el mismo perfil sin red, desbloqueo, nuevo login, PUSH, SQLite `[10,10,10]` y dashboard docente.

## Incidencias encontradas y resolución

- El primer pytest encontró `PermissionError` sobre un directorio temporal ajeno. Se interrumpió, diagnosticó con `-x` y repitió con `TEMP/TMP` en la carpeta de trabajo; no era un fallo del producto.
- La nueva suite E2E necesitó tipos de Node; se añadió `@types/node` y los tipos Vite al tsconfig E2E.
- TypeScript detectó una parametrización incorrecta de la tabla `it.each`; se corrigió para pasar cada lote completo al caso de prueba y se repitieron build y pruebas.
- El cierre anterior de servidores dependía de `taskkill /T`, que no terminaba los procesos en este entorno. Se detuvieron exclusivamente los dos servidores de prueba creados y se corrigió el lanzador para usar procesos directos y esperas acotadas. Las ejecuciones posteriores terminan y liberan los puertos.
- Flutter necesitó permiso de escritura en caché y una excepción `safe.directory` limitada al entorno del comando para el SDK del usuario, sin cambiar Git global. `flutter devices` siguió fallando en adb; no se presenta como «sin dispositivos» ni prueba física aprobada.

## No ejecutado / no demostrado

APK Android nuevo, Android físico, SQLCipher y migración móvil, evaluaciones equivalentes entrada/salida en navegador, adaptación curricular oficial 1–6, traducciones revisadas por especialistas, entrenamiento real autorizado, carga de producción, n8n real y auditoría de penetración completa.

Las pruebas Flutter de sincronización utilizan SQLite local y API falsa; no se confunden con el recorrido web que sí habla con FastAPI real. Los reportes anteriores del proyecto se conservan como antecedentes.
