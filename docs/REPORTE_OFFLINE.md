# Offline web — recorrido ejecutado

Estado del nuevo recorrido web: **IMPLEMENTADO Y VERIFICADO** en Chromium de Playwright sobre Windows y compilación de producción. Estado offline móvil y protección total del sistema: **PARCIALMENTE IMPLEMENTADO**.

## Uso

1. Iniciar sesión en línea como estudiante con actividades asignadas.
2. En «Aprender sin conexión», elegir y repetir una frase local de al menos 12 caracteres, larga y distinta del PIN. Pulsar «Descargar y proteger actividades» y esperar confirmación.
3. Abrir «Resolver actividad descargada». Cada respuesta se guarda cifrada antes de avanzar; no necesita API ni IA remota.
4. Tras cerrar el navegador, abrir de nuevo la misma dirección y perfil. En el acceso, expandir «Abrir actividades descargadas sin conexión», introducir la frase y desbloquear.
5. Recuperar conexión, introducir el código/PIN de la misma cuenta y verificar sesión. Pulsar «Sincronizar respuestas y actualizar».
6. Salir bloquea el almacén. «Quitar actividades descargadas» solo funciona sin respuestas pendientes y permite preparar otra cuenta en ese navegador.

La frase no se envía al servidor ni se guarda. No existe recuperación de una frase olvidada; conservarla es necesario para recuperar respuestas pendientes. Un navegador almacena un estudiante a la vez. El acceso local se renueva tras autenticación; el plazo local de siete días depende del reloj del dispositivo y no es una revocación remota fuerte.

## Ejecución reproducible

```powershell
cd teacher-web
npm ci
npx playwright install chromium
npm run test:offline
```

La prueba crea una base SQLite temporal, levanta FastAPI, carga datos ficticios, construye la web con su URL de API, instala el service worker y usa un perfil Chromium persistente. El estudiante descarga, responde diez sumas con toda la red del contexto desactivada, cierra Chromium y lo vuelve a lanzar sin red. El acceso exige frase; una incorrecta se rechaza. Después se verifica una sesión remota nueva y se sincroniza.

La consulta directa de SQLite confirma `[10, 10, 10]`: cantidad de intentos, UUID únicos y correctos. La prueba también consulta el progreso por API y abre el dashboard docente, cuyo total de intentos corresponde a datos persistidos. El origen y aprobación de la actividad se preparan por API; no se declara probado todo el proceso docente mediante clics.

## Servir manualmente la versión de producción

El service worker se registra en producción, bajo HTTPS o localhost. Si se usa `vite preview`, establecer `VITE_API_URL` a la URL del backend durante el build y autorizar ese origen web en `CORS_ORIGINS`. El nginx incluido usa la API del mismo origen mediante `/api/`. No usar el servidor Vite de desarrollo como prueba de reapertura offline.

El instalador espera el caché del shell antes de afirmar que la descarga está preparada. Se almacenan recursos públicos versionados por compilación; API y credenciales no se cachean. Los datos protegidos usan una base nueva, con cifrado autenticado y escrituras transaccionales; ver [seguridad](REPORTE_SEGURIDAD.md).

## Límites

No se cifra ni elimina silenciosamente la cola anterior de respuestas en línea. Si hay una respuesta antigua pendiente, hay que confirmarla antes de preparar la descarga. Con el almacén abierto, los enlaces de resolución en línea se redirigen al recorrido descargado para evitar colas paralelas.

No se verificó un dispositivo Android ni la recuperación tras matar por fuerza un proceso Flutter. SQLite móvil continúa sin cifrado. No hay validación de todos los navegadores, pérdida física del equipo, almacenamiento borrado por el sistema, cambio malicioso del reloj o dispositivo comprometido. El nuevo recorrido conserva rechazos para revisión; no transforma un rechazo del servidor en éxito local.
