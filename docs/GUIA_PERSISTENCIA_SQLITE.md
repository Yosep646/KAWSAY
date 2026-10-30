# KAWSAY AI — por qué «Guardar» puede perder datos y cómo comprobar SQLite

## Diagnóstico verificado, 30 de octubre de 2026

- `Yosep646/KAWSAY` usa **SQLite real**, no una base ficticia. Las rutas FastAPI guardan mediante SQLAlchemy y `db.commit()`.
- En la computadora local, `scripts/dev.py` ejecuta el backend desde `backend/`, y el valor `sqlite:///./data/kawsay.db` corresponde a **`backend/data/kawsay.db`**.
- El servicio Render `kawsay-ai-yosep-demo` se despliega desde `main`. La variante `kawsay-ai-offline-demo` usa la rama `codex/render-offline-20261030`. **Son dos bases separadas**. Los servicios antiguos `kawsay-* ` de `alcides18huerto-svg/-KAWSAY-AI` constituyen otra instalación independiente.
- Las instancias Render Free están configuradas con SQLite en **`/srv/data/kawsay.db`**, dentro del contenedor efímero. Crear un registro puede devolver **201 Created** y verse en pantalla, pero **reemplazar o reiniciar el contenedor puede hacer desaparecer ese archivo**. Ningún cambio de botones, `db.commit()`, `/ready` o migraciones arregla la ausencia de disco persistente.
- En los registros de Render del 28 de octubre se observan operaciones `POST /api/v1/classrooms`, `POST /api/v1/students` y documentos con `201 Created`. También se observan nuevos arranques de instancias. **No puede deducirse la recuperabilidad de un registro concreto sin backup**.

## Arrancar y verificar la base local desde VS Code

1. Abre la carpeta raíz `KAWSAY`, comprueba que el backend no esté ya en ejecución en el puerto 8000 y usa PowerShell.
2. La primera vez instala las dependencias y genera el secreto local:

   ```powershell
   py scripts/dev.py setup
   ```

3. Comprueba **la ruta exacta** del archivo SQLite y los conteos **sin mostrar información de estudiantes**:

   ```powershell
   py scripts/dev.py db
   ```

   Este comando aplica las migraciones incrementales existentes y ejecuta `python -m app.cli db-status` desde `backend/`. No elimina ni limpia registros.
4. Inicia la API **sin regenerar datos DEMO**:

   ```powershell
   py scripts/dev.py run
   ```

5. En otra terminal:

   ```powershell
   py scripts/dev.py web
   ```

6. Abre `http://127.0.0.1:8000/ready`, debe responder `ready` con `database: ok`. Luego crea un aula o actividad, recibe éxito de la API, recarga la página y comprueba que aparece en la consulta. Detén **solo el backend** con Ctrl+C y ejecuta `py scripts/dev.py run` otra vez: el registro debe seguir.
7. Respalda antes de cualquier cambio:

   ```powershell
   py scripts/dev.py backup
   ```

   La copia se guarda bajo `backups/` en la raíz del proyecto. Confirma que se generó el archivo y **consérvalo fuera del mismo equipo** con cifrado adecuado si contiene datos personales.

**Advertencias**:
- **No borres `backend/data/kawsay.db`** ni `backend/data/kawsay.db-wal` / `-shm` mientras el backend está corriendo. No muevas una SQLite en WAL por copiar solo el archivo `.db` con el proceso activo; usa la función de backup de SQLite.
- Si antes abriste el servidor desde otra carpeta y existe otro `data/kawsay.db`, **no lo sobrescribas sin una copia verificada**. Dos rutas distintas son dos bases distintas; solicita diagnóstico antes de migrar los datos.
- `py scripts/dev.py demo` es para cargar **ejemplos ficticios**; para retomar trabajo guardado utiliza `run`. No mezcles cuentas de demostración con información real de menores.
- El campo `storage_persistence: not_verified` de `db-status` es deliberado: una lectura exitosa de SQLite no demuestra la durabilidad física del disco.

## Render: qué falta para conservar datos entre despliegues

**No despliegues de nuevo antes de respaldar cualquier información recuperable en la instancia antigua.**

### Opción 1: Render con disco persistente (SQLite, mismo backend)

Necesitas un tipo de servicio compatible con **Persistent Disk** (puede suponer un coste). Configura el disco en el **mismo servicio** y monta, por ejemplo, `/var/data`. Fija:

```text
DATABASE_URL=sqlite:////var/data/kawsay.db
```

Mantén **una sola instancia** del backend y las migraciones Alembic al arrancar. Las copias de seguridad deben enviarse a **otra ubicación persistente y cifrada**. Antes de cambiar la ruta, recupera una copia consistente del SQLite anterior; crear la ruta nueva sin restaurar comenzará con una base vacía. Los cambios de plan/disco y cobros requieren tu autorización explícita.

### Opción 2: PostgreSQL administrado (producción escalable)

Existe una base PostgreSQL en tu cuenta Render, pero el código **actual** de `Yosep646/KAWSAY` rechaza URLs distintas de SQLite y sus migraciones fueron escritas para SQLite. **No basta con pegar `postgresql://...` en `DATABASE_URL`**: se necesita adaptar el motor, migraciones, esquema, bloqueos, pruebas y realizar una migración de datos controlada y respaldada. Además, una instancia PostgreSQL Free puede caducar. Nunca compartas cadenas de conexión o claves en el chat.

## Cómo reconocer el fallo

| Síntoma | Qué comprobar |
|---|---|
| Error 500 al guardar | Logs FastAPI, esquema/migraciones y la petición HTTP |
| Error 401/403 | Sesión y permisos, no necesariamente SQLite |
| Error 422 | Validación de formulario, no se creó el registro |
| 201/200 y desaparece al recargar **sin reiniciar** | Misma URL, mismos filtros/aula, GET correcto y base usada por backend |
| 201/200 y desaparece **tras redeploy/reinicio Render Free** | Archivo SQLite efímero; restaurar backup y migrar a disco persistente |
| Lo ves en una URL pero no en otra | Cada URL/proyecto tiene su propia base de datos |

## Pruebas automatizadas agregadas

`backend/tests/test_local_database_persistence.py` comprueba:
- que crear un aula por la API persiste el registro tras **cerrar y recrear** el motor SQLAlchemy;
- que `db-status` da ruta, migración e integridad reales;
- que una consulta diagnóstica no genera silenciosamente un SQLite vacío;
- que `scripts/dev.py run` prepara las migraciones antes de iniciar la API.

Ninguna de esas pruebas sustituye la verificación del disco físico de Render ni permite reconstruir datos que ya desaparecieron.
