# Verificación de continuación — 2026-10-26

Resultados observados en esta sesión, Windows; no sustituyen una revisión semántica completa ni validación en dispositivos.

| Comando | Resultado |
|---|---|
| `.venv\Scripts\python.exe -m pytest backend/tests ml/tests -q` | 147 aprobadas; advertencia de Starlette sobre transporte httpx. Línea base anterior al cambio de exportación. |
| `.venv\Scripts\python.exe -m pytest ml/tests/test_ml_pipeline.py -q` | 15 aprobadas después del cambio de exportación. |
| `npm test -- --run` en `teacher-web/` | 18 aprobadas; excluye integración HTTP. |
| `npm run build` en `teacher-web/` | TypeScript y compilación Vite correctos. |
| `npm run test:e2e` en `teacher-web/` | Integración HTTP: 1 prueba; Playwright Chromium: 5 pruebas aprobadas. El escenario offline del script simula una cola, no prueba Flutter. |
| `flutter --version` | No disponible en PATH; analyze, pruebas, compilación y dispositivo pendientes. |
| `git check-ignore backend/.env backend/data/kawsay.db ml/datasets/raw/real.jsonl` | Las tres rutas están ignoradas. |

La rama `audit/modernizacion-kawsay` existe sin commits; los archivos de proyecto aparecen sin seguimiento. Se preservan los archivos existentes y no se ha creado un commit inicial indiscriminado. No se han leído secretos ni borrado archivos durante esta sesión.

## Verificación adicional de inferencia

- Tras reforzar la selección de modelos se ejecutó de nuevo `.venv\Scripts\python.exe -m pytest backend/tests ml/tests -q`: **148 aprobadas**, una advertencia de Starlette. La primera ejecución tras el cambio produjo dos fallos porque los fixtures de integración marcaban como aprobado un modelo sintético; se ajustaron sus metadatos de prueba para simular explícitamente un modelo real aprobado, conservando el artefacto sintético aislado.
- `npm test -- --run`: 18 aprobadas; `npm run build`: compilación correcta.
- `npm run test:e2e`: integración HTTP 1 aprobada y Playwright Chromium 5 aprobadas; el cliente offline del escenario es simulado, no Flutter.
- `flutter --version`: comando no encontrado. `git check-ignore` confirmó la exclusión de las rutas privadas y de datos comprobadas.
- No se cambiaron dependencias ni se eliminaron archivos. La compilación web regeneró `teacher-web/dist/` y E2E generó resultados temporales ignorados.

## Continuación: automatización y funcionamiento real

- Se separó el filtro de firma del tipo de evento en el workflow n8n. Los eventos válidos que no son alertas se descartan y reciben 200; no hay notificación implementada. `python -m json.tool` validó la sintaxis, no la ejecución en n8n.
- `pytest backend/tests/test_automation_languages_tutor.py backend/tests/test_sync_reto10.py ml/tests -q`: 36 aprobadas, una advertencia de Starlette. No prueba Flutter ni n8n real.
- `where.exe flutter`: no encontrado; `docker info`: motor Docker inaccesible; `npx --no-install n8n --version`: n8n no instalado localmente. No se encontró dataset en `ml/datasets/`; no se examinó la base privada para inferir autorización.
- Entrenamiento real y prueba offline en dispositivo pendientes de datos autorizados y SDK/dispositivo; no se ha declarado ningún resultado simulado como real.

## Búsqueda adicional

- `scripts/audit_inventory.py` actualizó el inventario estructural: 273 archivos; no constituye lectura semántica individual de todos ellos.
- Se encontró `backend/data/kawsay.db`. Consultas SQLite en modo de solo lectura devolvieron 3 perfiles de estudiante, 23 intentos y 1 marco marcado como DEMO. No se mostraron registros personales. Estas cifras no cumplen el mínimo del exportador (200 estudiantes y 150 secuencias largas), ni demuestran autorización o procedencia de datos para entrenamiento.
- Búsqueda por extensiones dentro del proyecto encontró esa base, sin otros datasets CSV/JSONL/Parquet/XLSX visibles en la búsqueda; el inventario excluye directorios generados y secretos. `where.exe flutter`, `where.exe dart`, `where.exe adb` no encontraron ejecutables en PATH; la búsqueda de `flutter.bat` y `n8n.cmd` bajo el perfil de usuario tampoco encontró coincidencias. Esto no demuestra ausencia en todo el equipo.

## Intento de habilitar Flutter y protección del entrenamiento

- Se clonó Flutter oficial en un directorio temporal. Tres intentos de `flutter --version` agotaron 180 segundos cada uno durante la descarga de Dart o la preparación de Flutter; no se llegó a ejecutar analyze ni pruebas. No se instaló globalmente.
- `pytest ml/tests -q`: 17 aprobadas. El entrenamiento con `--source real` ahora comprueba directamente los mínimos de estudiantes y secuencias, también al recibir JSONL sin pasar por el exportador. Esta comprobación no certifica autorización ni procedencia de datos.

## Docker y nuevo intento móvil

- `docker desktop start` y `docker info`: motor disponible. `docker build -t kawsay-backend-audit:local ./backend` y `docker build -t kawsay-web-audit:local ./teacher-web`: correctos. No se ejecutó el despliegue integrado ni n8n.
- Añadido `teacher-web/.dockerignore`: evita enviar dependencias, artefactos y `.env` al contexto Docker. El build web posterior pasó.
- Otro intento de `flutter --version` agotó 240 segundos; Dart 3.13.7 sí inicia. `dart analyze lib` no es una validación de Flutter: falló porque Flutter y las dependencias del proyecto no están resueltas. Compilación y pruebas móviles siguen pendientes.

## Regresión adicional

- `docker run --rm ... alembic upgrade head` finalizó correctamente con SQLite temporal; un contenedor backend aislado respondió HTTP 200 a `/health` y fue detenido. No se comprobó persistencia compartida ni ejecución integrada con el panel.
- Se corrigió el verificador HMAC Python para rechazar timestamps malformados y no finitos. `.venv\Scripts\python.exe -m pytest backend/tests ml/tests -q`: **154 aprobadas**, una advertencia de Starlette. El receptor n8n real permanece sin ejecutar.

## Corrección de automatización

- El workflow fue importado satisfactoriamente con `n8nio/n8n:2.44.7 import:workflow` en contenedor efímero; no se ejecutó el webhook ni se envió una notificación.
- Una alerta sin canal de notificación devuelve 503 en lugar de confirmar una entrega inexistente. Se añadió reencolado de eventos fallidos únicamente para administradores; el receptor debe deduplicar por ID.
- `pytest backend/tests/test_automation_languages_tutor.py -q`: 17 aprobadas; una advertencia de Starlette. La prueba de despacho sigue usando transporte simulado.

## Contrato y auditoría del reintento

- El reencolado administrativo registra actor y evento en auditoría dentro de la misma transacción. Se amplió su prueba de integración.
- `pytest backend/tests ml/tests -q`: 155 aprobadas, una advertencia de Starlette. `npm test -- --run`: 18 aprobadas; esta suite excluye integración HTTP.
- `python scripts/gen_docs.py` regeneró el diagrama, índice API y OpenAPI a partir de los modelos y rutas actuales. No equivale a validar la ejecución de todos los endpoints.

## Sincronización: UUID con contenido distinto

- El servidor compara el intento recibido con el ya persistido antes de confirmar un reenvío como DUPLICATE. Si un UUID se reutiliza con contenido diferente, devuelve `event_id_conflict`, sin sobrescribir el intento existente.
- `pytest backend/tests/test_sync_reto10.py backend/tests/test_concurrency_sqlite.py -q`: 14 aprobadas. `pytest backend/tests ml/tests -q`: 156 aprobadas, una advertencia de Starlette. Los escenarios con Flutter y dos dispositivos físicos siguen pendientes.

## Reentrenamiento experimental

- `.venv\Scripts\python.exe -m ml.train --source synthetic --students 1000 --seed 7 --quick`: candidato `kawsay-diff-20261026221136-cce4aa`, dataset `ds-cce4aa467678`, 12 800 ventanas de desarrollo y 3 200 de test. F1 0,6600, precisión 0,5921, recall 0,7456 y accuracy 0,8509; heurística F1 0,6315. Son datos sintéticos y estas cifras no demuestran utilidad en aulas reales.
- Reprodujo las métricas del candidato previo con la misma semilla y protocolo; el nuevo artefacto permanece CANDIDATE. `python -m ml.make_model_card` actualizó la ficha; `pytest ml/tests backend/tests/test_forecast.py -q`: 24 aprobadas, una advertencia de Starlette.

## Sugerencia de dificultad

- El progreso docente devuelve una sugerencia por reglas para niveles 1–3, con mínimo de evidencia y decisión docente; el panel la muestra. No modifica ni asigna ejercicios automáticamente. La predicción ML existente es experimental y no controla este mecanismo.
- `pytest backend/tests ml/tests -q`: 157 aprobadas; `npm test -- --run`: 18 aprobadas; `npm run build`: correcto. Falta validación pedagógica y prueba de selección de ejercicios reales por nivel.

## Regresión posterior: paneles y cola web

- `.venv\Scripts\python.exe -m pytest backend/tests ml/tests -q`: 158 aprobadas; una advertencia de Starlette.
- `npm test -- --run` en `teacher-web`: 20 aprobadas. `npm run build`: TypeScript y Vite correctos.
- `npm run test:e2e`: una prueba de integración HTTP y seis pruebas Chromium aprobadas, incluida persistencia IndexedDB tras recargar. El flujo offline del script usa cola simulada; la prueba IndexedDB no valida recuperación y sincronización completa ni uso offline de la app estudiante.
- `flutter --version` con el SDK temporal agotó 120 segundos preparando Flutter. No se ejecutaron `flutter analyze`, `flutter test`, compilación Android ni pruebas en dispositivo.

## Instalación Flutter permanente

- Se instaló Flutter 3.47.8 en `C:\Users\euseb\flutter-sdk` y se añadió `bin` al PATH de usuario; las terminales existentes necesitan reiniciarse para actualizar su entorno. `flutter doctor -v` inicia: no encuentra Android SDK ni Visual Studio C++.
- `flutter pub get`: correcto; generó `mobile/pubspec.lock` y actualizó `analysis_options.yaml`. `flutter test`: 11 aprobadas, incluidas pruebas con SQLite y API falsa. `flutter analyze`: 8 avisos informativos, entre ellos acceso a BuildContext tras esperas y propiedades deprecadas.
- No hay compilación Android ni prueba en emulador/dispositivo; esas pruebas continúan pendientes.

## Herramientas Android

- Se instaló OpenJDK 17 y Android SDK de línea de comandos en `C:\Users\euseb\AppData\Local\Android\Sdk`, con platform-tools, plataformas 35 y 36 y build-tools 28.0.3 y 35.0.0. Flutter quedó configurado para usar el SDK y JDK. Durante la instalación se aceptaron las licencias presentadas por las herramientas del SDK.
- `flutter doctor -v` reconoce la cadena Android y las licencias. Android Studio no se instaló: su descarga por winget agotó 10 minutos. `adb devices` no muestra dispositivos. No hay emulador instalado, ni se ha generado la plataforma Android del proyecto o compilado un APK.
