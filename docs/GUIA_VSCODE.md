# Guía para ejecutar KAWSAY AI en VS Code

Para: **Yosep**. Tiempo: ~5 minutos. No necesitas instalar ninguna base de datos (SQLite viene con Python).

## Requisitos
| Programa | Versión | Para qué |
|---|---|---|
| Python | 3.10 o superior (recomendado 3.12) | backend y entrenamiento |
| Node.js | 20 o superior | panel docente |
| VS Code | cualquiera | + extensiones recomendadas (VS Code te las sugerirá al abrir la carpeta) |
| Flutter (opcional) | 3.22+ | solo para la app del estudiante (`mobile/`) |

## Pasos
1. Descomprime `KAWSAY-AI-final.zip` y abre la carpeta `KAWSAY-AI` en VS Code (**Archivo → Abrir carpeta**).
2. Abre una terminal (**Terminal → Nueva terminal**) y ejecuta, en este orden:
   ```bash
   python scripts/dev.py setup      # crea .venv, instala dependencias, genera backend/.env y crea la base SQLite
   python scripts/dev.py demo       # carga datos DEMO (aula 1.º+2.º+3.º, alertas) y deja el backend en http://127.0.0.1:8000
   ```
   En **Windows** si `python` no funciona prueba `py scripts/dev.py setup`.
3. Abre **otra** terminal para el panel docente:
   ```bash
   python scripts/dev.py web        # http://localhost:5173
   ```
4. Entra en `http://localhost:5173` con:
   - Docente: `maestra@demo.pe` / `Aula-Multigrado-2026!`
   - Administrador: `admin@demo.pe` / `Kawsay-Demo-Local-2026`
   (credenciales solo de demostración local).
5. Documentación interactiva de la API: `http://127.0.0.1:8000/docs`.

También puedes usar **Terminal → Ejecutar tarea…** (hay tareas «1) Instalar todo», «2) Cargar datos DEMO», «3) Panel docente») o
**Ejecutar y depurar (F5)** → «Backend KAWSAY (FastAPI)» para depurar con puntos de interrupción.

## Mantener los datos guardados entre sesiones de VS Code

Para trabajo normal, tras la primera instalación utiliza `py scripts/dev.py db` (muestra la ruta exacta de SQLite) y `py scripts/dev.py run` (arranca con migraciones verificadas). Inicia el frontend con `py scripts/dev.py web` en otra terminal. El comando `demo` solo es para introducir datos de ejemplo; no necesitas ejecutarlo cada vez.

Antes de cambiar equipos, reinstalar o subir a Render, crea un respaldo con `py scripts/dev.py backup`. **Render Free sin disco persistente no conserva la base local entre despliegues**. Diagnóstico completo: `docs/GUIA_PERSISTENCIA_SQLITE.md`.

## Qué verás en el demo
Una planificación activa por institución → un aula multigrado → una actividad que genera **una variante por grado** → revisión y aprobación
docente → publicación → los estudiantes reciben solo la variante de su grado → trabajo «sin Internet» (simulado) → sincronización sin duplicados →
una **alerta educativa con evidencia** («4 de los últimos 5 ejercicios presentan dificultad, 6 pistas…») en el Dashboard.

## Usar tus propios datos (sin demo)
`python scripts/dev.py admin` (crea tu administrador con una contraseña fuerte) → `python scripts/dev.py run` → entra al panel como administrador:
crea la escuela y los docentes, importa el marco curricular **oficial** (JSON revisado por una persona, con `is_demo: false`) y la planificación
de la institución. Para empezar de cero borra `backend/data/kawsay.db`.

## Ver la base de datos
Extensión «SQLite Viewer»: abre `backend/data/kawsay.db`. Respaldo: `python scripts/dev.py backup`.

## Entrenar / revisar el modelo de ML
```bash
python -m ml.train --source synthetic --students 2500 --seed 7     # ~1 minuto
python -m ml.robustness --seeds 7 11 23 --students 1500
python -m ml.make_model_card                                       # actualiza docs/ml-model-card.md
```
Es **experimental** (datos sintéticos). Lee `docs/ml-model-card.md` antes de sacar conclusiones.

## Pruebas
`python scripts/dev.py test` (backend, ML y panel).

### Panel en navegador real (Chromium)
Después de `setup`, desde otra terminal en la raíz:
```bash
npm --prefix teacher-web ci
npm --prefix teacher-web exec -- playwright install chromium
npm --prefix teacher-web run test:e2e
```
En Linux puede ser necesario instalar las dependencias del navegador con `playwright install --with-deps chromium`.
Las 5 pruebas usan backend real y una base SQLite temporal con datos **DEMO**, sin tocar `backend/data/kawsay.db`.
El ejecutor inicia y detiene sus servidores; deja libres los puertos **18000** y **15173** antes de ejecutarlo.
Cobertura y límites: `docs/16-testing.md`. Verificado en Windows con Chromium; no sustituye la prueba offline del móvil.

## App del estudiante (Flutter) — sin verificar
`cd mobile && flutter create . --platforms=android,windows && flutter pub get && flutter test`, luego
`flutter run --dart-define=KAWSAY_API=http://10.0.2.2:8000` (emulador Android). Esta app **nunca se compiló** en el entorno donde se
desarrolló: es posible que haya que corregir errores. Sigue la prueba offline manual de `mobile/README.md`.

## Problemas frecuentes
| Síntoma | Solución |
|---|---|
| `python` no se reconoce | instala Python y marca «Add to PATH»; en Windows usa `py` |
| Puerto 8000 ocupado | cierra el otro proceso o cambia el puerto en `scripts/dev.py` |
| `database is locked` | no abras la base con otro programa en modo escritura mientras corre el backend |
| Error de contraseña débil al crear un usuario | usa ≥ 12 caracteres, no comunes y sin tu correo |
| El panel no conecta | confirma que el backend corre en :8000 (el panel usa un proxy `/api`) |
