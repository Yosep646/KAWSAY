# Panel docente (React + TypeScript estricto + Vite)

Estado verificado: `tsc --noEmit` limpio, 13 pruebas (cliente API, tarjeta de alerta con evidencia, control de acceso, editor de preguntas,
gestión de estudiantes e idiomas),
build de producción, y una prueba de integración REAL contra el backend (login, aulas, resumen, alertas con evidencia, refresco de token).
**No** se probó en un navegador real (sin pruebas E2E con Playwright): el aspecto visual y la usabilidad están sin validar con docentes.

Páginas: Login · Dashboard (resumen real, alertas con evidencia, fortalezas, progreso) · Mis aulas (aulas multigrado, alta de estudiantes con
credenciales de un solo uso) · Estudiantes (alta, restablecimiento de PIN y elección lingüística declarada) · Planificación (versiones,
periodos/unidades/temas, aprobación y activación por admin) · Actividades (crear
por grados desde la planificación vigente, adaptar con KAWSAY AI, revisar/editar/aprobar, publicar) · Alertas educativas (intervenciones) ·
Administración (escuelas, docentes, importar marco curricular, auditoría, eventos de automatización).

```bash
npm ci && npm run dev            # proxy /api -> http://127.0.0.1:8000
npm run typecheck && npm test
VITE_API_URL=http://127.0.0.1:8000 VITE_TEST_TEACHER_EMAIL=... VITE_TEST_TEACHER_PASSWORD=... npm run test:integration
```
Seguridad: el access token vive solo en memoria; el refresh token en `sessionStorage` (trade-off: una cookie httpOnly sería más segura);
React escapa por defecto (sin `dangerouslySetInnerHTML`); CSP en `nginx.conf`.
Nota: si `npm install` es lento en discos de red, instala en un directorio local.
