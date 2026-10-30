# Restauración del logo original

Se recuperaron los dos archivos originales del repositorio KAWSAY que corresponden al logo mostrado por el usuario: el libro con hojas en azul y verde y la marca tipográfica blanca/turquesa. Se reutilizaron sin retocar sus píxeles ni generar imágenes nuevas.

| Archivo | Blob Git original |
|---|---|
| `teacher-web/src/assets/kawsay-brand-icon.webp` | `e41cdd7900ea81be9227332109046a8f7204b8d0` |
| `teacher-web/src/assets/kawsay-brand-wordmark.webp` | `d87f60827d38e3a97dbbe50e8e734303635ff1fd` |

El componente compartido `Brand` muestra el símbolo original en el menú. En el encabezado de acceso utiliza además la marca tipográfica original; sobre fondos claros conserva un nombre legible. El formulario de acceso muestra el mismo símbolo original.

Los archivos se importan como recursos Vite, con nombres versionados bajo `/assets/`. El servidor de Render los sirve con el tipo correcto y el service worker existente los incluye en el caché offline.

Comprobaciones ejecutadas: compilación de producción correcta, 28 pruebas web aprobadas e imágenes cargadas sin desbordamiento en 1440×1000 y 390×844. La actualización se publica en la rama de demostración `codex/render-offline-20261030`, sin modificar `main`.
