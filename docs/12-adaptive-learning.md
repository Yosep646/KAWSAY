# 12 · Aprendizaje adaptativo

## Ciclo (determinista y auditable)
pregunta → respuesta → evaluación → ¿necesita ayuda? → pista (nivel 1..3) → nuevo intento → cambio de estrategia → refuerzo → reevaluación → continuar.

### Implementado: sugerencia al docente

El progreso por competencia expone una sugerencia basada en `progress-v1`: con
menos de 5 ejercicios cerrados no sugiere nivel; por debajo de 0,5 propone nivel
1; por encima de 0,85, nivel 3; en el intervalo intermedio, nivel 2. Los niveles
son relativos a la escala curricular 1–3, no a la dificultad actual de cada
ejercicio. Se muestra en el panel docente. Es una regla orientativa: no modifica,
filtra ni genera ejercicios, ni selecciona automáticamente una actividad. El
docente debe elegir o preparar contenido apropiado y aprobarlo. Estos umbrales
requieren validación pedagógica; no son inferencia del modelo ML.

## Reglas iniciales (configurables, versionadas en `config/adaptive_rules.yaml`)
- Pista 1 tras 1 error; pista 2 tras 2 errores; tras 3 errores seguidos → estrategia alternativa (otra explicación/ejemplo) y actividad de refuerzo de menor complejidad.
- Estado interno por competencia: `REFUERZO` | `ESPERADO` | `DESAFÍO` (nunca mostrado con etiqueta negativa).
- Subir a DESAFÍO: ≥ N aciertos consecutivos con ≤ 1 pista en ventana reciente. Bajar a REFUERZO: tasa de acierto baja + uso alto de pistas en ventana.

## Progreso por competencia (propuesta a validar con docentes)
Ventana de últimos *K* intentos (p. ej. 20) por competencia con peso decreciente por antigüedad:
`score = Σ(w_i · s_i) / Σ w_i`, donde `s_i = 1` (acierto sin pista), `0.7` (acierto con 1 pista), `0.4` (acierto con ≥2 pistas), `0` (error). Se exige `evidence_count ≥ 5`; si no, se muestra "sin evidencia suficiente". `method_version` se guarda en cada fila. Los parámetros (K, pesos, mínimo) son configuración, no código.

## Fortalezas (patrones)
Mejora sostenida de `score`, disminución de pistas, mayor precisión, menor tiempo con precisión estable. Sin diagnósticos psicológicos.

## Support flag (ejemplo `R-SUP-001`)
En las últimas 5 actividades de una competencia, ≥ 4 con dificultad (error final o ≥ 2 pistas) → flag `open` con `evidence` (ids de intentos) y recomendación "actividad guiada". Lenguaje: "requiere práctica / revisión / se recomienda apoyo". Cada flag guarda `rule_id` y `rule_version`.

## Intervenciones
Se registran y se muestra la **evolución observada** (antes/después) sin afirmar causalidad.

## Motivación
Solo con comparaciones reales (p. ej. pistas 3→1). Variedad de plantillas, frecuencia limitada para evitar repetición.
