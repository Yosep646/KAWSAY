# KAWSAY AI — entrega incremental del ZIP recibido

Esta entrega continúa exclusivamente `KAWSAY_AI_CODIGO_FUENTE_COMPLETO_RESPALDO_2026-10-26.zip`. No incorpora archivos de OpenCode ni de otros proyectos locales. El respaldo original y la carpeta local de OpenCode permanecen intactos.

SHA-256 del ZIP de entrada: `7E11BC460AD9B3E11E5F97D417975F0E580CD1999E3DF7BE956335EC6C767A6F`.

Se completó el reconocimiento y se implementó una primera fase de seguridad de sesiones y aprendizaje web descargado: descarga protegida, diez respuestas sin red, cierre completo de Chromium, desbloqueo local y sincronización con FastAPI y SQLite reales. No se declara terminada la plataforma completa.

Empieza por [el estado y resultados actuales](docs/ESTADO_IMPLEMENTACION.md), [las instrucciones offline](docs/REPORTE_OFFLINE.md) y [la matriz de requisitos](docs/MATRIZ_REQUISITOS.md). Los informes del 26 de octubre son antecedentes; las cifras del contexto sobre OpenCode no corresponden a este ZIP.

## Instalar y ejecutar

Requisitos comprobados: Python 3.12, Node 24, npm y Chromium de Playwright. Flutter se verificó con 3.47.8 / Dart 3.13.7; las versiones mínimas declaradas siguen en `mobile/pubspec.yaml`.

Desde la raíz:

```powershell
python scripts/dev.py setup
python scripts/dev.py demo
```

En otra terminal, para la web habitual:

```powershell
python scripts/dev.py web
```

Para ejecutar la demostración offline automatizada, instala las dependencias y Chromium y deja libres los puertos 18000 y 15173:

```powershell
cd teacher-web
npm ci
npx playwright install chromium
npm run test:offline
```

El comando usa datos ficticios y bases temporales; construye y sirve la web de producción, ejecuta el recorrido completo y detiene los servidores al terminar. Para uso manual offline se requiere una compilación de producción bajo HTTPS o localhost; el servidor de desarrollo no instala el service worker. Consulta el reporte offline para configurar la URL del backend y CORS.

No se incluyen entornos privados, bases de estudiantes, claves, dependencias, cachés ni perfiles Chromium. Las credenciales DEMO presentes en las pruebas y scripts son exclusivamente ficticias y no corresponden a cuentas productivas. No se generó un APK en esta entrega.
