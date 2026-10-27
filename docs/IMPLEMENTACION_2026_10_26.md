# KAWSAY AI — Implementación incremental

## Cambios comprobables
- Paneles por rol existentes preservados; mejorados estilos visuales administrador, docente y estudiante.
- Biblioteca IndexedDB para **lectura** de actividades ya consultadas, aislada por identificador de estudiante; conexión requerida para autenticación e inicio de actividades nuevas.
- Script `python -m ml.train_authorized --data ...` que exige un archivo real autorizado, valida suficiencia e inicia el pipeline auténtico ya existente.
- La cola de respuestas pendiente existente se conserva; **no** hay un modo offline completo ni sincronización automática garantizada.

## Limitaciones
- El archivo adjunto no contiene dataset real autorizado; los modelos presentes se identifican como SYNTHETIC/CANDIDATE. No se entrenó un modelo real con datos de alumnos.
- La persistencia IndexedDB de actividades no equivale a un modo offline completo (no hay PWA operativa ni autenticación offline).
- Los datos académicos almacenados localmente requieren revisar políticas de privacidad y dispositivos compartidos antes de producción.
- Necesario comprobar compilación Vite, pruebas backend y pruebas reales con usuario docente/estudiante en dispositivo antes de desplegar.
