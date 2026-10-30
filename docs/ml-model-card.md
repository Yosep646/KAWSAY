# Ficha del modelo — kawsay-diff-20261026221136-cce4aa

**Estado: CANDIDATE · datos: SYNTHETIC.** **NO está aprobado ni se usa para decidir nada.**

_Documento generado por `python -m ml.make_model_card` desde `ml/reports/`. No editar a mano._

## Uso previsto
Estimar, a partir de los últimos 10 ejercicios cerrados de una competencia, la probabilidad de que ≥ 3 de los próximos 5 presenten dificultad. Es una **señal de apoyo para el docente**, junto a las alertas por reglas con evidencia. No es un diagnóstico, no etiqueta al estudiante y no decide qué se enseña.

## Uso NO previsto
Diagnóstico clínico o psicológico, calificación, decisiones disciplinarias, comparación entre estudiantes, uso sin revisión docente, o uso con datos de aulas distintas a las validadas.

## Datos
- Tipo: **SYNTHETIC** (simulador de estudiantes con capacidad latente, rachas de bajón y uso de pistas; puntuación con las mismas funciones de producción).
- Estudiantes: 1000 · ventanas: desarrollo 12800, test 3200.
- Versión del dataset: `ds-cce4aa467678` · semilla 7.
- Entradas (11): mean_score_10, mean_score_5, min_score_10, std_score_10, frac_difficult_10, frac_difficult_5, hints_per_ex_10, wrong_per_ex_10, trend_10, last3_mean, grade. Sin nombre, identificador, idioma, ubicación ni otros datos personales.

## Entrenamiento
- Partición por estudiante (sin fuga): 80 % desarrollo / 20 % test; búsqueda con validación cruzada agrupada (3 pliegues) entre 2 configuraciones; elegido: `logreg_C1.0` por PR-AUC.
- Calibración: sigmoid (Platt), CV agrupada externa e interna. Umbral 0.32 elegido con predicciones fuera de muestra.
- El conjunto de test se usó una sola vez.

## Resultados en test (datos sintéticos)
| Métrica | Valor | IC 95 % (remuestreo de estudiantes) |
|---|---|---|
| ROC-AUC | 0.9103 | 0.8792 – 0.9323 |
| PR-AUC | 0.7044 | 0.6308 – 0.7743 |
| F1 | 0.66 | 0.6132 – 0.7108 |
| Precisión / Recall | 0.5921 / 0.7456 | — |
| Brier / ECE (calibración) | 0.0916 / 0.0134 | — |

| Comparación | Precisión | Recall | F1 |
|---|---|---|---|
| Modelo | 0.5921 | 0.7456 | 0.66 |
| Regla R-SUP-001 (últimos 5) | 0.7116 | 0.4251 | 0.5323 |
| Heurística: media de 5 < 0.5 | 0.6179 | 0.6457 | 0.6315 |

**Lectura honesta:** la diferencia puntual de F1 frente a la heurística simple es 0.0285. No se ha calculado un intervalo pareado para esa diferencia; no demuestra superioridad estadística ni utilidad educativa. La regla vigente resuelve otra tarea (dificultad actual, no futura).

## Errores por banda de grado (test)
| Banda | n | Falsos negativos (tasa) | Falsos positivos (tasa) |
|---|---|---|---|
| grados_1-2 | 928 | 0.172 | 0.1456 |
| grados_3-4 | 1040 | 0.2722 | 0.0804 |
| grados_5-6 | 1232 | 0.3008 | 0.146 |

Las tasas por banda no certifican ausencia de sesgo; con datos reales hay que repetir este análisis por aula y por contexto antes de usar el modelo (aquí no hay esos atributos y, por diseño, el modelo no los usa).

## Limitaciones
- Entrenado con datos SINTÉTICOS: mide cuánto recupera la estructura del simulador, NO el desempeño en aulas reales.
- Predice dificultad en los próximos ejercicios; no es un diagnóstico del estudiante.
- Requiere revisión humana (docentes/pedagogos) antes de cualquier uso; no sustituye al docente.
- La relación entre dificultad futura y apoyo útil no está validada: faltan datos de intervenciones reales.

## Condiciones para aprobarlo
1. Datos reales suficientes (≥ 200 estudiantes y ≥ 150 secuencias largas, con consentimiento y seudonimización).
2. Reentrenar y evaluar con esos datos, comparando contra las reglas auditables.
3. Revisión humana de docentes y pedagogos; solo entonces `registry.approve(...)`.
4. Monitoreo en uso y reentrenamiento programado.
