# Pendientes después de esta entrega

## Siguiente fase: protección móvil y coherencia educativa

1. Cifrar SQLite móvil con una biblioteca mantenida y claves protegidas por el sistema operativo. Diseñar migración no destructiva, integridad, recuperación y pruebas de reapertura con diez respuestas. El cifrado web no resuelve este punto.
2. Añadir desbloqueo móvil local y verificar cierre completo de Flutter. Resolver el acceso a adb y preparar/compilar Android desde esta copia; ejecutar en dispositivo físico cuando exista acceso comprobable.
3. Cerrar Mis cursos por matrícula/grado/área en web y Flutter reutilizando asignaciones y currículo. Las actividades del respaldo sí llegan por API, pero no existe aquí una verificación de un módulo completo de cursos.
4. Implementar y probar entrada → actividades → salida → consulta docente desde interfaces, con evaluaciones pedagógicamente equivalentes. No renombrar actividades ordinarias para dar ese criterio por cumplido.

## Seguridad e integración

- Migrar o sustituir con garantías la cola web anterior sin perder respuestas; ampliar el cifrado a todos los datos locales sensibles.
- Gestionar dispositivos y revocación individual, revisar vinculación de su identidad al token, conflictos entre dispositivos y versionado/retiro de actividades.
- Completar aislamiento administrativo por institución, pruebas de API y auditorías del despliegue real.
- Hacer revisión independiente de cifrado, sesiones, XSS, extensiones, retención, respaldos y dispositivos compartidos antes de usar datos reales de menores.

## Validaciones y servicios externos

- Matriz curricular MINEDU trazable por grado y competencia, con revisión pedagógica. Las reglas aritméticas del respaldo no equivalen a adaptación 1–6 curricular validada.
- Validación lingüística de materiales existentes por especialistas; no certificar traducciones automáticas.
- Datos reales autorizados para ML, evaluación separada por estudiante, comparación con reglas y aprobación documentada. Los artefactos incluidos siguen siendo experimentales.
- n8n real con receptor, canal y confirmación de entrega comprobados. Las funciones educativas no deben depender de su disponibilidad.
- Medición de carga, memoria de teléfonos modestos, despliegue institucional y recuperación de respaldos.

El escenario demostrado en esta entrega es una base técnica verificable para el Reto 02. La evidencia y alertas por reglas del respaldo contribuyen al Reto 10, sin acreditar impacto educativo, diagnóstico ni aptitud productiva completa.
