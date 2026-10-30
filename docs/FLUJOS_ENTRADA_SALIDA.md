# Entrada, persistencia y salida comprobadas

## Actividad y resultados

Docente autenticado → planificación vigente → actividad → variante revisada/aprobada → publicación → asignación autorizada por grado. Esta cadena usa los servicios del respaldo y se verifica en `backend/tests/test_assignments.py` y en la demo HTTP aislada. La prueba offline prepara la actividad docente por API, sin simular respuestas del servidor.

Estudiante autenticado → `/sync/pull` → descarga explícita → instantánea cifrada de contenido y estados → diez respuestas en cola persistente → cierre completo → desbloqueo local → nuevo login en línea de la misma cuenta → PUSH → corrección y transacción SQLite → estados oficiales → confirmación individual local → resumen docente.

En el escenario ejecutado, SQLite consultada en solo lectura devolvió diez intentos, diez UUID distintos y diez respuestas correctas del estudiante ficticio. El segundo envío desde el botón encontró cero pendientes. La idempotencia ante reenvío del mismo UUID también se prueba en `backend/tests/test_sync_reto10.py` y en la demo HTTP.

## Fallos

Sin red al enviar: se conserva la cola. ACK incompleto, ajeno o repetido: no se borra ningún evento del lote. Lote parcialmente rechazado: se conservan únicamente los rechazados tras persistir estados y confirmaciones válidas. Frase incorrecta o contenido alterado: no se abre el almacén. Otra cuenta remota: no se envían las respuestas. Acceso local vencido: se preserva la cola y se exige renovación tras autenticación.

## Evaluaciones

No se implementó ni verificó en esta fase una evaluación diagnóstica y otra final pedagógicamente equivalentes. Los resultados de actividades no se denominan automáticamente evaluación de entrada/salida ni evidencia causal de mejora. Este recorrido permanece pendiente.
