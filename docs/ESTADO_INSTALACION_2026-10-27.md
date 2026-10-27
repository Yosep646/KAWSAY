# Estado de instalación y pruebas — 27/10/2026

## Entorno verificado
- La versión de Node en este entorno es 22.16.0, no 24.15.0; una actualización en la PC del usuario no modifica este entorno aislado.
- `npm run build` no pasa: faltan archivos de tipos `vite/client`, `vitest/globals`, `@testing-library/jest-dom` porque `node_modules` está incompleto.
- No se ha confirmado una compilación React ni una prueba PWA en navegador.

## Cambios efectuados
- Se corrigió el instalador `instalar_kawsay_windows.ps1` para ejecutar pruebas frontend y pruebas de integración, además de las pruebas backend de autenticación, actividades y sincronización, después de instalar los requisitos.
- El ZIP entregado excluye el `node_modules` incompleto y las cachés generadas, con el objetivo de que `npm ci` instale dependencias desde cero en Node 24.15+.

## Pruebas ejecutadas
`python -m pytest -q backend/tests/test_sync_reto10.py backend/tests/test_auth.py backend/tests/test_assignments.py`

Resultado: **37 passed in 12.37s**.

## En la PC con Node actualizado
Desde la carpeta raíz del proyecto, ejecutar PowerShell:
`powershell -ExecutionPolicy Bypass -File .\instalar_kawsay_windows.ps1`

Esto requiere acceso al registro npm, Python y acceso al índice pip. La ejecución local no ha sido verificada en este entorno. Las pruebas offline del navegador siguen pendientes; las pruebas de backend no son prueba de funcionamiento offline completo.
