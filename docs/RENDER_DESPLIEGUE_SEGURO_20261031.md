# KAWSAY AI — despliegue seguro conservando la URL de Render

## Servicio identificado (31/10/2026)

- URL existente: **https://kawsay-ai-yosep-demo.onrender.com**
- Render service ID: `srv-dbgdld8473hc73d5pjbg`
- GitHub: `Yosep646/KAWSAY`, rama `main`
- AutoDeploy: **desactivado** (el push no cambia la URL pública).
- Plan: **Free**, archivo SQLite en `/srv/data/kawsay.db` en el contenedor **efímero**.
- Último despliegue público comprobado: 28/10/2026 (commit `c2dabbec`).
- El código actual de `main` ya incorpora Tutor IA, matrículas, cursos, idiomas, respaldo administrativo, Ollama y workflow n8n. **No se ha desplegado** a esta URL.
- Existe un PostgreSQL `kawsay-postgres` Free de Render que caduca **19/11/2026**. KAWSAY actualmente sólo admite SQLite: **no** pegar su URL PostgreSQL sin una migración explícita.

## Bloqueo antes del despliegue

**NO PULSAR 'Deploy latest commit' todavía**. Render Free elimina el archivo SQLite al suspenderse, reiniciarse o desplegar. El backend público antiguo no incorpora el endpoint de exportación administrativa, que sólo está en el código nuevo. Desplegar el código nuevo para obtener ese endpoint podría borrar antes los datos a recuperar.

La herramienta conectada de Render permite leer la configuración, consultar logs y ejecutar despliegues, pero **no ofrece acceso de archivos/SSH a la instancia**, ni un comando para adjuntar discos o cambiar planes. Por tanto no es posible verificar ni rescatar los bytes de SQLite desde estas acciones. La existencia de guardados HTTP 201 no equivale a una copia restaurable.

El usuario debe recuperar los datos por una vía autorizada antes de sustituir la instancia. Si el panel no ofrece acceso de Shell/SSH ni exportación, **no existe garantía de recuperar registros persistentes del contenedor Free**: es preciso conservar la instalación y evaluar otras copias locales o registros previamente exportados. No compartir claves de administrador ni datos de menores con terceros.

## Ruta recomendada (sin cambiar de URL)

**Requiere aprobar explícitamente los costes de un plan de web service de pago y un disco persistente Render.** El conector disponible no permite ni ejecutar ese cambio de plan ni montar un disco. El dueño de la cuenta lo hace en:

`https://dashboard.render.com/web/srv-dbgdld8473hc73d5pjbg`

1. Recuperar **primero** una copia completa y consistente `.db` de la base anterior **antes de realizar cualquier cambio de plan o redeploy**. Las tablas deben incluir `users`, `schools` y `alembic_version`. Verificar `PRAGMA integrity_check` y `PRAGMA foreign_key_check` en un equipo local.
2. En **Render → servicio → Settings / Instance Type**, seleccionar el plan de pago autorizado. En la sección **Disk**, añadir un disco persistente, por ejemplo con montaje `/var/data`. La modificación puede reiniciar el servicio: no hacerlo sin la copia.
3. Restaurar la copia al punto de montaje como `/var/data/kawsay.db` por un mecanismo oficial de Render, con permisos del usuario `kawsay`. No sobrescribir una copia existente sin otra copia externa. El disco sólo se monta en runtime, no en build/predeploy.
4. En **Environment** establecer (con `JWT_SECRET` anterior conservado):
   ```dotenv
   DATABASE_URL=sqlite:////var/data/kawsay.db
   KAWSAY_STORAGE_MODE=persistent
   KAWSAY_PERSISTENT_MOUNT=/var/data
   ```
5. El nuevo `render.Dockerfile` ejecuta `python -m app.production_preflight` **antes** de Alembic. Si falta disco, no está montado, la ruta es equivocada, la copia no existe o está corrupta, **el arranque se detiene**. Así no se sustituye la información por una base vacía. Con `persistent`, no se ejecuta `app.demo_bootstrap`.
6. Sólo después de verificar **copia + montaje + env vars**, ejecutar el despliegue manual de la rama `main` en el servicio **original**. No crear un segundo servicio si se necesita mantener la URL.
7. Probar `/health`, `/ready`, roles, cursos, matrícula, tutor, idiomas y respaldos. Guardar una matrícula **ficticia**, recargar; realizar un reinicio controlado, comprobar que persiste. Descargar un respaldo desde `/admin/respaldos`, restaurarlo en una instalación aislada y verificar integridad.
8. Con el Tutor IA, en Render Free o pagado, **Ollama no se instala solo**. Para IA generativa en Render hace falta configurar un proveedor de IA autorizado o un servicio Ollama privado accesible desde Render. Sin proveedor, quedan las pistas pedagógicas; n8n necesita webhook, secreto HMAC y SMTP configurados.

## Si todavía no hay ninguna copia recuperable

Detener el despliegue y evitar nuevos reinicios. Opciones:
- Exportación previa por vía autenticada si existe un método en la versión efectivamente publicada.
- Copias `.db` que ya se descargaron desde equipos de desarrollo, backups personales o importaciones anteriores.
- Si no hay datos para preservar, se necesita una aprobación **separada y explícita** para iniciar una base nueva vacía; el modo `persistent` de KAWSAY **se niega por defecto a hacerlo**.

## Prueba de seguridad del código

`backend/tests/test_render_preflight.py` prueba que el proceso no arranca cuando no hay disco, cuando la BD no fue restaurada, cuando la ruta apunta fuera del montaje o cuando la copia está dañada; prueba también que acepta una SQLite de KAWSAY íntegra en el volumen indicado.

## Qué NO puede garantizar este cambio de código

- No recupera por sí solo la SQLite antigua del contenedor.
- No cambia el plan de Render ni paga por un disco.
- No instala Ollama, n8n ni credenciales SMTP.
- No asegura copias automáticas externas; para datos escolares reales todavía hay que definir cifrado, retención, recuperación y controles de privacidad.

Para el resto de instrucciones: [GUÍA DE PERSISTENCIA](GUIA_PERSISTENCIA_SQLITE.md) y [TUTOR IA](TUTOR_IA_OLLAMA_AUTOMATIZACION_REAL_20261031.md).
