# KAWSAY AI · Estado verificable del entrenamiento (28-10-2026)

## Resultado actual
- **Entrenamiento ejecutado:** GitHub Actions run [40777600164](https://github.com/Yosep646/KAWSAY/actions/runs/40777600164).
- Datos: **SYNTHETIC**, 1.000 estudiantes simulados (semilla 7), NUNCA información de niños reales.
- Protocolo: 10 ejercicios cerrados para predecir dificultad en los próximos 5, partición **POR ESTUDIANTE** 80 % desarrollo / 20 % test; CV agrupada y calibración con pliegues agrupados; control de fuga; baselines; informe y ficha del modelo.
- Resultado: se generaron `ml/models/*.joblib`, `ml/reports/*.json`, la ficha `docs/ml-model-card.md` y el registro `ml/registry/registry.json` **como artefacto descargable de la ejecución**, almacenado por GitHub Actions durante 30 días; no se versionaron datos de estudiantes.
- Seguridad: **CANDIDATE**; `predict.predict(..., allow_experimental=False)` impide usarlo en producción. No se ha concedido aprobación humana.
- ML no genera directamente ejercicios: proporciona pronóstico opcional; la automatización de sumas/restas/multiplicaciones/divisiones por grado está en `backend/app/modules/assignments/math_grade_rules.py`.
- El pronóstico opcional `/api/v1/analytics/classrooms/{classroom_id}/forecast` incluye señal de dificultad y recomendación de refuerzo por **RULES**, con evidencias y decisión final del docente; nunca reasigna automáticamente.

## Datos reales: pendiente por depender de autorización y evidencia suficiente
El código de exportación/pseudonimización y de entrenamiento de datos reales existe, pero **no se ha ejecutado un entrenamiento validado con datos reales de estudiantes peruanos**: no existe un dataset local autorizado de tamaño suficiente accesible al flujo actual.

Para habilitarlo de forma ética y reproducible:
1. Obtener autorización institucional, base legal adecuada, medidas de privacidad, seguridad de almacenamiento y consentimiento cuando corresponda. Nunca guardar DNI, nombres, ubicaciones o idioma en el dataset de entrenamiento.
2. En un entorno de datos persistente y privado, comprobar >= **200 estudiantes** y >= **150 secuencias** con al menos 15 ejercicios cerrados. Cada serie se separa por estudiante.
3. Exportar desde una copia autorizada de SQLite: `DATABASE_URL=sqlite:////ruta/segura/kawsay.db ML_PSEUDONYM_SALT=<sal_privada> python -m ml.export_real --out /ruta/privada/real.jsonl`.
4. `python -m ml.train_authorized --data /ruta/privada/real.jsonl`.
5. Revisar las métricas fuera de muestra, calibración, errores por grados, pertinencia pedagógica, distribución local, riesgo de sobreajuste y sesgos antes de aprobar manualmente. El estado por defecto es **CANDIDATE**.
6. Desplegar sólo tras configurar persistencia de datos en Render, revisar la política de datos y aprobar la versión. No confiar en SQLite efímera de Render Free.

Los conjuntos de ASSISTments son referencias de investigación de otros países y edades; su acceso/uso puede requerir aceptar condiciones. No se presentan como malla curricular de primaria peruana ni como validación local.

## Comandos de reproducción sintética sin datos privados

```bash
pip install -r backend/requirements.txt -r ml/requirements.txt
python -m ml.train --source synthetic --students 1000 --seed 7 --quick
python -m ml.make_model_card
python -m pytest ml/tests -q
```

**Límite pedagógico:** ni la probabilidad ML ni una regla modifican el grado oficial o publican actividades sin intervención del docente.
