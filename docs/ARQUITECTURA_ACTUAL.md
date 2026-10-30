# Arquitectura de esta entrega

Se conserva el monolito modular FastAPI, SQLAlchemy/Alembic y SQLite del respaldo, React/TypeScript/Vite y Flutter con SQLite local. No se sustituyó ninguna aplicación ni base de datos. Ver [arquitectura existente](05-architecture.md), [modelo de datos](06-database-design.md) y [decisión SQLite](19-decisions/ADR-010-SQLite-servidor.md).

La web tiene ahora dos recorridos explícitos:

1. En línea: contratos y pantallas originales; la cola anterior `kawsay-student-pending` se conserva y no se presenta como cifrada.
2. Descargado: `OfflinePanel` consume `/sync/pull` y los estados de intentos; `offlineVault` guarda una instantánea cifrada en la base nueva `kawsay-encrypted-offline`. `OfflineActivity` guarda cada evento antes de pasar a la pregunta siguiente. `offlineLearning` verifica identidad remota y confirma cada evento al sincronizar.

El service worker solo conserva HTML, JavaScript y CSS públicos de la compilación. No cachea API, tokens o identidades. La clave local existe únicamente en memoria mientras el almacén está abierto. No hay tokens persistentes en el almacén nuevo: tras reiniciar, el estudiante debe autenticarse en línea nuevamente antes del PUSH.

La fuente oficial del resultado sigue siendo FastAPI/SQLite. La web descargada muestra respuestas pendientes, sin adjudicar notas provisionales como oficiales. La API recalcula corrección y progreso con las reglas existentes. El ML no interviene en el desbloqueo ni en la corrección offline.

No hubo cambios de esquema SQL ni migraciones nuevas. El formato cifrado es versión 1 y rechaza versiones desconocidas conservando el registro. La cola anterior no se transforma ni se elimina; una respuesta anterior pendiente impide preparar la nueva descarga hasta confirmarla.
