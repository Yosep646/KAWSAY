# Seguridad — cambios y límites

## Sesiones del backend

Se corrigió un problema concreto del respaldo: revocar refresh tokens no invalidaba de inmediato los access tokens existentes. Ahora `sid` identifica la familia y cada petición comprueba su vigencia en SQLite. Las pruebas verifican logout, rotación normal, reutilización de refresh y reset de PIN. El reset no revoca la sesión del docente. No hubo cambios de esquema.

## Almacén web nuevo

`offlineVault.ts` usa PBKDF2-HMAC-SHA-256 con 600.000 iteraciones, sal aleatoria de 16 bytes y AES-256-GCM con IV aleatorio de 12 bytes por escritura. Identificador del dueño y revisión se autentican como datos asociados. La frase y la clave derivada no se persisten; la clave es no exportable en Web Crypto y solo se mantiene en memoria mientras está abierto. El metadato exterior expone un UUID de dueño y parámetros criptográficos, sin nombre, código de acceso o respuestas.

Las primitivas y su uso de datos asociados se basan en la [especificación Web Crypto del W3C](https://www.w3.org/TR/webcrypto-2/). El factor PBKDF2 se referencia a [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html); esta elección no constituye una auditoría criptográfica independiente ni una certificación del producto.

Web Locks serializa cambios de varias pestañas y cada escritura comprueba la revisión esperada en una transacción IndexedDB. No se admite degradación a almacenamiento sin cifrado cuando falla esa capacidad. La lectura y escritura esperan confirmación transaccional. La prueba del navegador verifica ausencia de nombre, contenido y frase en el registro exterior, rechazo de otra frase, rechazo de otro dueño y detección de un byte alterado. Otra prueba conserva dos respuestas simultáneas desde dos pestañas.

Tras reiniciar se exige autenticación remota nueva antes del PUSH; la frase local no es una credencial del servidor. La identidad remota debe coincidir con la del almacén. Expiración local y rechazos no borran respuestas pendientes.

## Pendientes explícitos

- La cola web original `kawsay-student-pending` continúa sin cifrado. No se migró ni eliminó automáticamente. La protección nueva es optativa para actividades descargadas, no una afirmación de cifrado de todos los datos web existentes.
- SQLite Flutter sigue sin SQLCipher ni otra protección integral de sus páginas. La custodia de claves, migración, reapertura y recuperación móvil requieren implementación y pruebas propias.
- No se implementó revocación individual de dispositivos. El protocolo conserva el `device_id` del contrato existente; la sesión se vincula a usuario/familia, sin nuevo claim de dispositivo.
- El plazo local de siete días depende del reloj local. Una copia offline no puede consultar una revocación del servidor hasta reconectar.
- XSS, extensiones maliciosas, malware o acceso a una pestaña ya desbloqueada quedan fuera de la protección del cifrado en reposo. Cada pestaña mantiene su propia clave en memoria; bloquear una no expulsa otras ya abiertas.
- No hay recuperación de una frase perdida ni resistencia garantizada a una frase débil y ataque offline a una copia robada. Se recomienda una frase larga y no evidente, asistida por adulto cuando corresponda.
- Las pruebas de aislamiento y permisos no sustituyen una auditoría independiente ni validación legal. No se usaron datos de menores ni se realizaron pruebas en producción.

La fuente de estados es [MATRIZ_REQUISITOS.md](MATRIZ_REQUISITOS.md); las reglas generales existentes siguen en [14-security.md](14-security.md).
