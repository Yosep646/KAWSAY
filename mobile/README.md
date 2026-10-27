# App del estudiante (Flutter) — pruebas locales aprobadas; Android no verificado

Flutter 3.47.8 está instalado y se ejecutaron las pruebas locales: **11 aprobadas**. `flutter analyze` reportó 8 avisos. No se ha compilado Android ni ejecutado la app en un dispositivo. Lo que SÍ está verificado:
- el contrato HTTP que usa (`/auth/student-login`, `/sync/push`, `/sync/pull`, `/learning/*`, `/tutor/turn`, `/languages`) está probado
  en `backend/tests` y con `scripts/demo_e2e.py` (que simula a este cliente);
- la lógica local (corrección, progreso, pistas, motivación) tiene vectores compartidos con el servidor (`shared/rules_vectors.json`),
  comprobados en Python y Dart (`test/rules_test.dart`). Las pruebas de sync utilizan API falsa y SQLite de prueba, no un dispositivo Android.

## Qué implementa (sin verificar en dispositivo)
SQLite local (perfil, tareas, preguntas, intentos, progreso, cola de sync) · intento+evento en UNA transacción · UUID de evento
(idempotencia) · SyncManager (PENDING→SYNCING→SYNCED/FAILED, backoff, recuperación tras cierre brusco) · ConnectivityMonitor ·
sesión local con tokens en almacenamiento seguro · Home (MIS TAREAS / QUIERO APRENDER / MI PROGRESO / TUTOR) · actividad con corrección y
pistas locales · progreso sencillo y positivo · idioma elegido por la persona (solo traducciones verificadas).
**No implementa:** Learning Packs con imágenes/audio (las tareas se descargan por `/sync/pull`), IA en el dispositivo, notificaciones,
cifrado de SQLite (pendiente: SQLCipher), iOS/macOS no probados.

## Primer uso (en una máquina con Flutter)
```bash
cd mobile && flutter create . --platforms=android,windows   # genera carpetas de plataforma (no se incluyen)
flutter pub get && flutter analyze && flutter test
flutter run --dart-define=KAWSAY_API=http://10.0.2.2:8000    # emulador Android -> backend local
```
**Prueba offline obligatoria (manual):** entrar con Internet → esperar la descarga → modo avión → responder → cerrar la app → reabrir
(la respuesta sigue) → quitar modo avión → confirmar que el servidor recibió el intento una sola vez.
