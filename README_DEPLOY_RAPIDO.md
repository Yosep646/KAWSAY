# KAWSAY AI — cómo instalar en un servidor local sin pagar alojamiento

**Uso recomendado: piloto con datos de prueba y computadora propia.** Para información real de niñas y niños exige controles de acceso, protección física, copias de seguridad y una evaluación de privacidad.

## Opción 1. Windows + Docker Desktop (recomendada)

1. Instala y abre [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Descomprime este ZIP. Desde PowerShell, dentro de `KAWSAY-AI`, ejecuta:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\iniciar_kawsay_windows.ps1
   ```
3. El primer inicio descarga imágenes y paquetes; necesita **Internet**. La aplicación instalada seguirá disponible en la LAN sin Internet externo si tu red local está funcionando (funciones de IA externas seguirán sin conexión).
4. Abre **http://127.0.0.1:8080** en esa computadora.
5. Ejecuta `python scripts/smoke_local_stack.py` para verificar web + API + base de datos.
6. Crea el primer administrador manualmente con una contraseña única, robusta y no reutilizada. En PowerShell:
   ```powershell
   $env:ADMIN_PASSWORD = Read-Host 'Contraseña segura del administrador'
   docker compose exec -e ADMIN_PASSWORD backend python -m app.cli create-admin admin@ejemplo.pe "Administrador"
   Remove-Item Env:ADMIN_PASSWORD
   ```
   No uses contraseñas de ejemplo con datos reales.

**Teléfonos de la misma red Wi-Fi:** cambia `WEB_BIND_IP=0.0.0.0` dentro de `.env` y ejecuta `docker compose up -d`; accede a `http://IP-DE-TU-PC:8080`. Permite solo la red LAN confiable en el firewall. Una PWA con Service Worker requiere contexto seguro (HTTPS) en móviles; **un acceso HTTP por IP no habilita necesariamente el modo offline PWA**. Para uso sensible, habilita HTTPS antes de usar credenciales reales desde teléfonos.

Para revisar registros: `docker compose logs -f --tail=100 backend teacher-web`. Para detener: `docker compose down` (**sin `-v`**, que borraría el volumen de la base de datos). Para iniciar de nuevo: `docker compose up -d`.

## Opción 2. Linux + Docker

```bash
bash scripts/run_local.sh
python scripts/smoke_local_stack.py
```

El backend no se expone públicamente por defecto; Nginx sirve React y reenvía las rutas `/api/` a FastAPI, desde la misma URL. La base SQLite queda persistente en el volumen Docker `kawsay_data` (haz copias de seguridad antes de actualizaciones).

## Render gratuito: solo demostración controlada

Render ofrece sitios estáticos y servicios web gratuitos, pero apaga las instancias inactivas, su almacenamiento de archivos es efímero y las bases PostgreSQL gratuitas expiran. **No usar SQLite en un Web Service Free para guardar datos de estudiantes.** Este repositorio mantiene SQLite como base del servidor y no está listo para escalar en Render Free de forma persistente. Para una prueba pública, usa únicamente datos ficticios y define una arquitectura de almacenamiento persistente externa antes de publicar.

## Qué verificó la auditoría

Consulta `docs/REPORTE_AUDITORIA_Y_PRUEBAS_LOCAL.md` para resultados, limitaciones y seguridad. La compilación final `vite build` y la prueba offline con Chromium deben completarse en tu entorno con Node compatible, dependencias Linux/Windows y navegador permitido.
