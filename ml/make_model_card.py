"""Genera docs/ml-model-card.md a partir de los reportes REALES de entrenamiento (nada escrito a mano)."""
from pathlib import Path

from ml import registry
from ml.common import REPORTS_DIR, read_json

ROOT = Path(__file__).resolve().parent.parent


def main() -> Path:
    items = registry.list_models()
    if not items:
        raise SystemExit("No hay modelos registrados: ejecuta python -m ml.train")
    meta = items[-1]
    r = read_json(REPORTS_DIR / f"{meta['model_id']}.json")
    rob_path = REPORTS_DIR / "robustness.json"
    rob = read_json(rob_path) if rob_path.exists() else None
    if rob and rob.get("protocol") != r["params"].get("protocol"):
        rob = None  # no atribuir al modelo actual evaluaciones de un protocolo anterior
    t, ci, b = r["test"], r["test_ci95"], r["baselines_test"]
    rule, heur = b["regla_R-SUP-001_ultimos5"], b["heuristica_media5<0.5"]
    lines = [
        f"# Ficha del modelo — {r['model_id']}", "",
        f"**Estado: {meta['status']} · datos: {r['data_kind']}.** " + ("**NO está aprobado ni se usa para decidir nada.**" if meta["status"] != "APPROVED" else ""), "",
        "_Documento generado por `python -m ml.make_model_card` desde `ml/reports/`. No editar a mano._", "",
        "## Uso previsto", "Estimar, a partir de los últimos 10 ejercicios cerrados de una competencia, la probabilidad de que ≥ 3 de los "
        "próximos 5 presenten dificultad. Es una **señal de apoyo para el docente**, junto a las alertas por reglas con evidencia. "
        "No es un diagnóstico, no etiqueta al estudiante y no decide qué se enseña.", "",
        "## Uso NO previsto", "Diagnóstico clínico o psicológico, calificación, decisiones disciplinarias, comparación entre estudiantes, "
        "uso sin revisión docente, o uso con datos de aulas distintas a las validadas.", "",
        "## Datos", f"- Tipo: **{r['data_kind']}** (simulador de estudiantes con capacidad latente, rachas de bajón y uso de pistas; "
        "puntuación con las mismas funciones de producción).", f"- Estudiantes: {r['params']['students']} · ventanas: desarrollo {r['samples']['dev']}, test {r['samples']['test']}.",
        f"- Versión del dataset: `{r['dataset_version']}` · semilla {r['params']['seed']}.",
        f"- Entradas ({len(r['features'])}): {', '.join(r['features'])}. Sin nombre, identificador, idioma, ubicación ni otros datos personales.", "",
        "## Entrenamiento", f"- Partición por estudiante (sin fuga): 80 % desarrollo / 20 % test; búsqueda con validación cruzada agrupada ({r['cv']['folds']} pliegues) "
        f"entre {len(r['cv']['results'])} configuraciones; elegido: `{r['chosen']}` por PR-AUC.", f"- Calibración: {r['calibration']}. Umbral {r['threshold']} elegido con predicciones fuera de muestra.",
        "- El conjunto de test se usó una sola vez.", "",
        "## Resultados en test (datos sintéticos)", "| Métrica | Valor | IC 95 % (remuestreo de estudiantes) |", "|---|---|---|",
        f"| ROC-AUC | {t['roc_auc']} | {ci['roc_auc'][0]} – {ci['roc_auc'][1]} |", f"| PR-AUC | {t['pr_auc']} | {ci['pr_auc'][0]} – {ci['pr_auc'][1]} |",
        f"| F1 | {t['f1']} | {ci['f1'][0]} – {ci['f1'][1]} |", f"| Precisión / Recall | {t['precision']} / {t['recall']} | — |",
        f"| Brier / ECE (calibración) | {t['brier']} / {t['ece']} | — |", "",
        "| Comparación | Precisión | Recall | F1 |", "|---|---|---|---|",
        f"| Modelo | {t['precision']} | {t['recall']} | {t['f1']} |", f"| Regla R-SUP-001 (últimos 5) | {rule['precision']} | {rule['recall']} | {rule['f1']} |",
        f"| Heurística: media de 5 < 0.5 | {heur['precision']} | {heur['recall']} | {heur['f1']} |", "",
         f"**Lectura honesta:** la diferencia puntual de F1 frente a la heurística simple es {round(t['f1'] - heur['f1'], 4)}. "
         "No se ha calculado un intervalo pareado para esa diferencia; no demuestra superioridad estadística ni utilidad educativa. La regla vigente resuelve otra tarea "
        "(dificultad actual, no futura).", ""]
    if rob:
        s = rob["summary"]
        lines += ["## Robustez entre semillas", f"{len(rob['seeds'])} semillas ({', '.join(map(str, rob['seeds']))}), {rob['students']} estudiantes cada una:",
                  f"- F1 del modelo: {s['model_f1']['mean']} ± {s['model_f1']['std']} (mín. {s['model_f1']['min']}, máx. {s['model_f1']['max']}).",
                  f"- F1 de la heurística: {s['heuristic_f1']['mean']} ± {s['heuristic_f1']['std']}; de la regla: {s['rule_f1']['mean']} ± {s['rule_f1']['std']}.",
                  f"- Ganancia media de F1 del modelo sobre la heurística: {s['f1_gain_over_heuristic']}.", ""]
    lines += ["## Errores por banda de grado (test)", "| Banda | n | Falsos negativos (tasa) | Falsos positivos (tasa) |", "|---|---|---|---|"]
    for k, v in r["error_by_grade_band"].items():
        lines.append(f"| {k} | {v['n']} | {v['tasa_fn']} | {v['tasa_fp']} |")
    lines += ["", "Las tasas por banda no certifican ausencia de sesgo; con datos reales hay que repetir este análisis por aula y por "
              "contexto antes de usar el modelo (aquí no hay esos atributos y, por diseño, el modelo no los usa).", "",
              "## Limitaciones", *[f"- {x}" for x in r["limitations"]],
              "- La relación entre dificultad futura y apoyo útil no está validada: faltan datos de intervenciones reales.", "",
              "## Condiciones para aprobarlo", "1. Datos reales suficientes (≥ 200 estudiantes y ≥ 150 secuencias largas, con consentimiento y seudonimización).",
              "2. Reentrenar y evaluar con esos datos, comparando contra las reglas auditables.", "3. Revisión humana de docentes y pedagogos; solo entonces `registry.approve(...)`.",
              "4. Monitoreo en uso y reentrenamiento programado."]
    out = ROOT / "docs" / "ml-model-card.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print("escrito", main())
