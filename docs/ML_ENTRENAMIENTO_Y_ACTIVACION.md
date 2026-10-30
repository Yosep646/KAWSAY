# KAWSAY AI — Entrenamiento de ML, recomendaciones y activación segura

## Estado verificable (30-10-2026)

- **Automatización curricular:** el motor de reglas de Matemática genera variantes para 1.º–6.º en borrador y exige revisión docente. No es un modelo ML.
- **ML candidato:** `ml/train.py` entrena un clasificador con ventanas de 10 ejercicios cerrados, estimando si al menos 3 de los 5 siguientes tendrán dificultad. El modelo generado con datos **sintéticos** es **CANDIDATE**, NO está aprobado para uso educativo real.
- **Prueba de entrenamiento en GitHub Actions:** ejecución [41060168198](https://github.com/Yosep646/KAWSAY/actions/runs/41060168198), artefacto descargable en su pestaña *Artifacts*, con el `.joblib`, JSON de métricas, registro y ficha técnica. Artefactos retenidos durante 30 días. No es un despliegue.
- **Seguimiento docente:** `GET /api/v1/analytics/classrooms/{id}/forecast` entrega `guidance` basada en respuestas realmente registradas aun cuando `available: false` (ML no disponible). Las sugerencias de refuerzo, mantenimiento o desafío son orientativas y requieren decisión docente.
- **Producción Render:** la imagen Docker no incluye las dependencias ni el modelo ML. No se ha habilitado predicción experimental ni se ha reiniciado el servicio. El entorno gratuito con SQLite efímero no debe utilizarse como almacén permanente de expedientes estudiantiles.

## 1. Entrenar y evaluar el candidato sin datos reales

Desde la raíz del repositorio (Python 3.12):

```bash
python -m pip install -r ml/requirements.txt
python -m ml.train --source synthetic --students 450 --seed 7 --quick
python -m ml.make_model_card
python -m pytest ml/tests -q
```

El pipeline separa por **estudiante**, usa validación cruzada agrupada y calibración, compara con reglas simples y registra el modelo como **CANDIDATE**. El AUC/F1 resultante refleja solo la estructura de los datos del simulador. No compara pedagogía real.

Los archivos `ml/models/` y `ml/datasets/` están excluidos de Git por contener artefactos privados, potencialmente identificables o de distribución restringida.

## 2. Preparación de datos reales: solo con autorización y almacenamiento privado

**No** subas nombres, DNI, correos, documentos de alumnos, bases de datos ni JSONL de rendimiento al repositorio, a GitHub Actions ni a un chat. El administrador de la institución debe autorizar los usos de los datos y definir retención, acceso y eliminación.

La exportación genera seudónimos HMAC, excluye identidad/idioma/ubicación y exige al menos:
- **200** estudiantes diferentes.
- **150** secuencias de al menos 15 ejercicios cerrados (10 de historia y 5 futuros).

En un equipo o servidor bajo control de la institución, con una copia autorizada de SQLite y una sal secreta no versionada:

```bash
export DATABASE_URL="sqlite:////ruta/privada/kawsay.db"
export ML_PSEUDONYM_SALT="una-sal-larga-secreta-generada-para-este-entrenamiento"
python -m ml.export_real --out ml/datasets/raw/real.jsonl
python -m ml.train_authorized --data ml/datasets/raw/real.jsonl
```

En Windows PowerShell se pueden definir las variables con `$env:DATABASE_URL` y `$env:ML_PSEUDONYM_SALT`. La ruta del dataset debe permanecer protegida y no compartirse. La etiqueta `REAL` identifica el origen declarado del archivo, **no demuestra consentimiento ni calidad de datos**. La revisión debe verificarlos por separado.

Si no se cumple la muestra mínima, **no entrenar ni sustituir con datos sintéticos de manera silenciosa**.

## 3. Evaluar antes de aprobar

Exigir revisión pedagógica independiente de la ficha del modelo: métricas en alumnos no vistos, falsos negativos/positivos por grado, calibración, posible fuga de información, utilidad educativa, privacidad y efectos no deseados. El entrenamiento **no** cambia el estado `CANDIDATE` a `APPROVED` automáticamente.

El registro de modelos solo permite aprobar modelos declarados como `REAL` con un revisor identificado, pero **el propio registro no reemplaza** la verificación de origen y la evaluación institucional. Guardar registro y modelo en almacenamiento privado y persistente, no en el filesystem efímero de Render Free.

## 4. Recomendaciones sin modelo aprobado

La aplicación ofrece siempre apoyo docente basado en reglas auditables **si existen suficientes ejercicios reales completados**:

| Resultado observado | Recomendación docente | Dificultad orientativa |
|---|---|---|
| Evidencia insuficiente | Esperar más actividades | Sin nivel |
| Dificultad recurrente | Probar un refuerzo **del mismo grado y competencia** | 1/3 |
| Rendimiento esperado | Mantener la actividad | 2/3 |
| Dominio consistente | Considerar un desafío **del mismo grado y competencia** | 3/3 |

Solo después de aprobar y desplegar de forma segura un modelo con datos reales podrá añadirse una **probabilidad ML adicional**. Esa probabilidad no asignará tareas automáticamente ni cambiará el grado de matrícula.

## 5. Verificaciones

- Pruebas backend: `backend/tests/test_forecast_teacher_guidance.py`, `backend/tests/test_domain_adaptive.py`.
- Pruebas ML: `ml/tests/test_ml_pipeline.py` (incluye rechazo de modelos sintéticos aprobados, datos inválidos, fuga por estudiante, y validación del entrenamiento).
- Pipeline CI: `.github/workflows/ci.yml`.
- Entrenamiento reproducible sintético: `.github/workflows/train-ml-candidate.yml`.

**Pendiente para un uso real completo:** almacenamiento persistente y copias de seguridad, dataset real autorizado y suficiente, entrenamiento/validación externa, aprobación por profesionales del centro, distribución protegida del archivo del modelo y pruebas de implementación con cuentas autorizadas.
