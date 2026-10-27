# React: solución del bloqueo de instalación

## Hallazgo reproducido (27-10-2026)
- Node local `22.16.0` no cumple los requisitos de versiones actuales de Vite 8 y plugin React 6.
- El entorno de revisión no resuelve DNS para `registry.npmjs.org`; `npm ci` no puede recuperar paquetes no cacheados (`xmlchars`), incluso tras cambiar Node.
- **No se ha obtenido una compilación exitosa en este entorno**. El problema externo de red no puede resolverse únicamente editando TypeScript.

## Ajustes efectuados
- CI ahora instala Node 24.15.0 (en vez de Node 22).
- `.nvmrc`, `package.json#engines` y `.npmrc` detectan incompatibilidad antes de instalar.
- `npm run preflight` muestra diagnóstico explícito.
- CI ejecuta también `test:integration`.

## Compilar en un entorno con acceso a npm
```bash
cd teacher-web
nvm install && nvm use
npm ci
npm run preflight
npm run typecheck
npm test
npm run test:integration
npm run build
```

Para pruebas E2E: `npx playwright install --with-deps chromium` seguido de `npm run test:e2e`, asegurando que los servicios configurados en Playwright estén levantados.

Verifica salida de `npm config get registry` y conectividad DNS si `npm ci` no termina. No suprimas el lockfile ni uses `--force` para ocultar fallos de versión.
