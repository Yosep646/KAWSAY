# ML — verificación del respaldo

`python -m pytest ml/tests -q`: **17 aprobadas**. Se conservó el código y los artefactos ML del ZIP; no hubo entrenamiento nuevo ni acceso a datos personales.

La suite cubre el pipeline experimental, características, partición por estudiante, registro, carga, inferencia y restricciones de datos/modelos. Véanse `ml/tests/test_ml_pipeline.py`, [ml.md](ml.md), [ficha existente](ml-model-card.md) y los reportes JSON incluidos en `ml/reports/`.

Las métricas sintéticas del 26 de octubre son antecedentes, no resultados obtenidos de nuevo en esta entrega. No acreditan utilidad pedagógica real ni un modelo aprobado. La inferencia experimental no se convirtió en adaptación curricular ni en diagnóstico. Las reglas deterministas y las decisiones docentes se mantienen.

Estado de modelo validado con datos reales: **BLOQUEADO POR DEPENDENCIA EXTERNA**. Se requieren datos autorizados y trazables, revisión de calidad y evaluación pedagógica. No se inventaron datasets, autorizaciones ni métricas.
