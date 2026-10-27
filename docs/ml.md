# ML — estado real

**Estado: EXPERIMENTAL. Ningún modelo está aprobado ni se usa para decidir. No existen datos reales suficientes.**
Resultados, límites y condiciones de aprobación: **`docs/ml-model-card.md`** (se genera solo desde los reportes reales).

## Qué hay (verificado: `ml/tests`, 9 pruebas)
simulador sintético → ventanas pasado→futuro → versión de dataset (hash) → partición **por estudiante** (80 % desarrollo / 20 % test) →
búsqueda de hiperparámetros con **validación cruzada agrupada** (regresión logística y gradient boosting) → calibración (Platt) → umbral con
predicciones fuera de muestra → test usado **una sola vez** → IC 95 % por remuestreo de estudiantes → comparación con la regla vigente y una
heurística simple → errores por banda de grado → robustez entre semillas (`ml.robustness`) → registro (CANDIDATE) → inferencia separada.

## Salvaguardas
- Un modelo entrenado con datos no reales **no puede aprobarse** (`registry.approve` lo rechaza).
- `predict` solo carga modelos APPROVED; el backend (`GET /analytics/classrooms/{id}/forecast`) responde `available=false` sin uno, y el modo
  experimental (`ML_ALLOW_EXPERIMENTAL=true`) siempre devuelve una advertencia.
- `export_real` filtra primaria (grados 1–6) antes de comprobar ≥ 200 estudiantes y ≥ 150 secuencias largas; seudonimiza con HMAC (sal secreta de al menos 16 caracteres) y no exporta nombre, código, ubicación ni idioma. Secundaria requiere un esquema y evaluación específicos.
- El backend no depende de `ml/` ni de scikit-learn.

## Resultado honesto
Con datos sintéticos el modelo logra ROC-AUC ≈ 0.91 y F1 ≈ 0.69, pero la ganancia sobre una heurística simple (media de los últimos 5 < 0.5) es de
~0.01–0.02 de F1 y no es significativa entre semillas. **No demuestra superar a las reglas auditables.** Con datos reales hay que repetirlo.

## Comandos
`python -m ml.train` · `python -m ml.robustness` · `python -m ml.make_model_card` · `python -m ml.export_real` (solo con datos reales).
Deep learning: no está justificado para este problema hoy (reglas → estadística → ML clásico → DL, en ese orden).
