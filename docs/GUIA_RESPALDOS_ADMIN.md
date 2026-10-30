# Respaldos administrativos reales en KAWSAY AI

## Qué ofrece la página /admin/respaldos

- `GET /api/v1/admin/storage/status`: verifica que SQLite está accesible y si se puede crear una copia. La durabilidad del disco figura como **no verificada**.
- `GET /api/v1/admin/storage/export`: descarga una copia íntegra consistente de SQLite mediante `sqlite3.Connection.backup()`, verificada por integridad y claves foráneas, sin almacenarla como una falsa copia permanente.
- Solo el ADMIN autenticado puede usarla. Los demás roles reciben 403 y el público 401.

## Advertencia crítica sobre Render Free

En Render Free la SQLite almacenada dentro del contenedor desaparece al suspenderse, reiniciarse o desplegarse. Descargar una copia no hace persistente al servidor. Las copias deben guardarse fuera, preferiblemente cifradas.

**NO despliegues esta modificación sobre tu servicio actual si quedan datos por recuperar.** El despliegue podría destruir el archivo antiguo antes de que el nuevo endpoint esté disponible. Esta exportación protege datos de la nueva instancia después del despliegue; no puede rescatar automáticamente una SQLite de una instancia anterior.

## Descarga segura

1. En una instancia que ya incluya el nuevo código, inicia sesión con ADMIN.
2. En Respaldos, verifica 'SQLite conectada' y el botón 'Descargar respaldo .db'.
3. Confirma el aviso y guarda el archivo descargado en una unidad cifrada fuera de Render.
4. Verifica la restauración en un entorno aislado de prueba, sin sustituir bases de datos activas.
5. No compartas un archivo .db con información escolar por enlaces públicos o GitHub.

## Almacenamiento duradero

- Alternativa SQLite: Render de pago con disco persistente, montado en la ruta exacta de DATABASE_URL y con copias externas verificadas. Requiere consentimiento antes de generar costes.
- Alternativa PostgreSQL: adaptar motor, operaciones, migraciones, pruebas y datos antes de conectarla. La base PostgreSQL Free de Render caduca a los 30 días y no es producción.
- El proyecto NO asegura todavía backups automáticos ni restauración en la web.

## Pruebas

- `backend/tests/test_storage_backup.py`: copia real con registros, controles de acceso, integridad SQLite.
- `teacher-web/src/test/storageBackups.test.tsx`: estados conectados al backend y confirmación antes de exportación.

Esta rama no despliega Render ni borra los datos existentes.