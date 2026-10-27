"""Pipeline de entrenamiento (honesto y reproducible).

datos -> ventanas (pasado->futuro) -> versión de dataset (hash) -> partición POR ESTUDIANTE (train+val 80 % / test 20 %)
-> búsqueda de hiperparámetros con validación cruzada AGRUPADA por estudiante (solo sobre train+val)
-> calibración de probabilidades -> umbral elegido con predicciones fuera de muestra (OOF) -> TEST usado una sola vez
-> intervalos de confianza por remuestreo de estudiantes -> baselines -> error por banda de grado -> registro (CANDIDATE).

Uso: python -m ml.train --source synthetic --students 3000 --seed 7
     python -m ml.train --source real --data ml/datasets/raw/real.jsonl      (solo con datos reales suficientes)
"""
import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml import export_real, registry, synthetic
from ml.common import FEATURES, HISTORY, HORIZON, MODELS_DIR, REPORTS_DIR, TARGET_MIN_DIFFICULT
from ml.features import build_windows, dataset_version, group_split, validate_sequences


def _candidates(quick: bool, seed: int) -> dict:
    grid = {}
    for c in ((1.0,) if quick else (0.1, 1.0, 10.0)):
        grid[f"logreg_C{c}"] = lambda c=c: make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=2000, class_weight="balanced"))
    for depth in ((3,) if quick else (2, 3, 4)):
        for lr in ((0.1,) if quick else (0.05, 0.1)):
            grid[f"hgb_d{depth}_lr{lr}"] = lambda depth=depth, lr=lr: HistGradientBoostingClassifier(
                max_depth=depth, learning_rate=lr, max_iter=150, random_state=seed, class_weight="balanced")
    return grid


def metrics(y, proba=None, pred=None) -> dict:
    out = {}
    if proba is not None:
        out |= {"roc_auc": round(float(roc_auc_score(y, proba)), 4), "pr_auc": round(float(average_precision_score(y, proba)), 4),
                "brier": round(float(brier_score_loss(y, proba)), 4), "ece": round(expected_calibration_error(y, proba), 4)}
    if pred is not None:
        tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
        out |= {"accuracy": round(float(accuracy_score(y, pred)), 4),
                "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
                "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
                "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
                "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}}
    return out


def expected_calibration_error(y, proba, bins: int = 10) -> float:
    idx = np.minimum((np.asarray(proba) * bins).astype(int), bins - 1)
    ece = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            ece += m.mean() * abs(np.asarray(y)[m].mean() - np.asarray(proba)[m].mean())
    return float(ece)


def best_threshold(y, proba) -> float:
    ts = np.linspace(0.05, 0.95, 91)
    return float(ts[int(np.argmax([f1_score(y, proba >= t, zero_division=0) for t in ts]))])


def bootstrap_ci(y, proba, pred, groups, n: int = 200, seed: int = 0) -> dict:
    """IC 95 % remuestreando ESTUDIANTES (las ventanas de un mismo estudiante están correlacionadas)."""
    rng = np.random.default_rng(seed)
    ids = np.unique(groups)
    by = {g: np.flatnonzero(groups == g) for g in ids}
    vals = {"roc_auc": [], "pr_auc": [], "f1": []}
    for _ in range(n):
        pick = rng.choice(ids, size=len(ids), replace=True)
        ix = np.concatenate([by[g] for g in pick])
        if len(set(y[ix].tolist())) < 2:
            continue
        vals["roc_auc"].append(roc_auc_score(y[ix], proba[ix]))
        vals["pr_auc"].append(average_precision_score(y[ix], proba[ix]))
        vals["f1"].append(f1_score(y[ix], pred[ix], zero_division=0))
    return {k: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)] for k, v in vals.items()}


def load_sequences(source: str, students: int, seed: int, data: Path | None):
    if source == "synthetic":
        return synthetic.simulate_sequences(students, seed), "SYNTHETIC"
    if source != "real" or data is None:
        raise ValueError("La fuente real requiere un archivo autorizado --data")
    return [json.loads(line) for line in Path(data).read_text(encoding="utf-8").splitlines() if line.strip()], "REAL"


def grouped_folds(X, y, groups, n_splits):
    """También la calibración anidada separa estudiantes; falla con datos insuficientes."""
    if len(np.unique(groups)) < n_splits:
        raise ValueError("Estudiantes insuficientes para validación agrupada")
    folds = list(GroupKFold(n_splits=n_splits).split(X, y, groups))
    for tr, va in folds:
        if len(np.unique(y[tr])) < 2 or len(np.unique(y[va])) < 2:
            raise ValueError("Cada partición de validación necesita ambas clases")
        if set(groups[tr]) & set(groups[va]):
            raise ValueError("Fuga de estudiantes en validación")
    return folds


def run(source="synthetic", students=3000, seed=7, data=None, write=True, quick=False) -> dict:
    seqs, kind = load_sequences(source, students, seed, data)
    if kind == "REAL":
        validate_sequences(seqs)
        export_real.check_sufficiency(
            len({s["student"] for s in seqs}),
            sum(len(s["results"]) >= HISTORY + HORIZON for s in seqs),
        )
    X, y, groups, meta = build_windows(seqs)
    if len(set(y.tolist())) < 2:
        raise SystemExit("La etiqueta tiene una sola clase; no se puede entrenar")
    params = {"history": HISTORY, "horizon": HORIZON, "target_min_difficult": TARGET_MIN_DIFFICULT, "kind": kind,
              "seed": seed, "students": len({s["student"] for s in seqs}), "protocol": "grouped-calibration-v2"}
    ds_version = dataset_version(X, y, params)

    masks, parts = group_split(groups, seed, fracs=(0.8, 0.0, 0.2))   # 80 % entrenamiento+validación (CV) / 20 % test
    assert not (parts["train"] & parts["test"])
    dev = masks["train"] | masks["val"]
    Xd, yd, gd = X[dev], y[dev], groups[dev]
    Xte, yte, gte = X[masks["test"]], y[masks["test"]], groups[masks["test"]]

    # --- selección de hiperparámetros: CV agrupada por estudiante, SOLO con datos de desarrollo
    n_splits = 3 if quick else 5
    if len(np.unique(yte)) < 2:
        raise ValueError("El conjunto de prueba necesita ambas clases")
    splits = grouped_folds(Xd, yd, gd, n_splits)
    cv_results = {}
    for name, make in _candidates(quick, seed).items():
        oof = np.zeros(len(yd))
        for tr, va in splits:
            m = make().fit(Xd[tr], yd[tr])
            oof[va] = m.predict_proba(Xd[va])[:, 1]
        cv_results[name] = {**metrics(yd, proba=oof), "f1_at_best_threshold": round(float(f1_score(yd, oof >= best_threshold(yd, oof))), 4)}
    chosen = max(cv_results, key=lambda k: cv_results[k]["pr_auc"])

    # --- modelo final calibrado (Platt) con CV agrupada; umbral con predicciones fuera de muestra
    final = CalibratedClassifierCV(_candidates(quick, seed)[chosen](), method="sigmoid", cv=splits)
    final.fit(Xd, yd)
    oof_cal = np.zeros(len(yd))
    for tr, va in splits:
        inner = grouped_folds(Xd[tr], yd[tr], gd[tr], 3)
        oof_cal[va] = CalibratedClassifierCV(_candidates(quick, seed)[chosen](), method="sigmoid", cv=inner).fit(Xd[tr], yd[tr]).predict_proba(Xd[va])[:, 1]
    thr = best_threshold(yd, oof_cal)

    # --- TEST (una sola vez)
    p_te = final.predict_proba(Xte)[:, 1]
    pred_te = (p_te >= thr).astype(int)
    test = metrics(yte, proba=p_te, pred=pred_te)
    ci = bootstrap_ci(yte, p_te, pred_te, gte, n=60 if quick else 200, seed=seed)
    te_meta = [m for m, k in zip(meta, masks["test"], strict=True) if k]
    rule_pred = np.array([m["rule_flag"] for m in te_meta])
    baselines = {"regla_R-SUP-001_ultimos5": metrics(yte, pred=rule_pred),
                 "heuristica_media5<0.5": metrics(yte, pred=(Xte[:, FEATURES.index("mean_score_5")] < 0.5).astype(int)),
                 "siempre_positivo": metrics(yte, pred=np.ones_like(yte))}
    grades = np.array([m["grade"] for m in te_meta])
    by_band = {}
    for lo, hi in ((1, 2), (3, 4), (5, 6)):
        k = (grades >= lo) & (grades <= hi)
        pos = int(yte[k].sum())
        fn = int(((pred_te[k] == 0) & (yte[k] == 1)).sum())
        fp = int(((pred_te[k] == 1) & (yte[k] == 0)).sum())
        by_band[f"grados_{lo}-{hi}"] = {"n": int(k.sum()), "positivos": pos, "tasa_fn": round(fn / max(pos, 1), 4),
                                        "tasa_fp": round(fp / max(int((yte[k] == 0).sum()), 1), 4)}
    model_id = f"kawsay-diff-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{ds_version[3:9]}"
    report = {"model_id": model_id, "data_kind": kind, "dataset_version": ds_version, "params": params,
              "runtime": {"python": platform.python_version(), "numpy": np.__version__,
                          "scikit_learn": sklearn.__version__, "joblib": joblib.__version__},
              "samples": {"dev": int(len(yd)), "test": int(len(yte))}, "prevalence_test": round(float(yte.mean()), 4),
              "cv": {"folds": n_splits, "grouped_by": "student", "results": cv_results}, "chosen": chosen,
              "calibration": "sigmoid (Platt), CV agrupada externa e interna", "threshold": round(thr, 3), "test": test, "test_ci95": ci,
              "baselines_test": baselines, "error_by_grade_band": by_band, "features": FEATURES,
              "limitations": ["Entrenado con datos SINTÉTICOS: mide cuánto recupera la estructura del simulador, "
                              "NO el desempeño en aulas reales." if kind == "SYNTHETIC" else "Datos reales; validar por aula antes de usar.",
                              "Predice dificultad en los próximos ejercicios; no es un diagnóstico del estudiante.",
                              "Requiere revisión humana (docentes/pedagogos) antes de cualquier uso; no sustituye al docente."]}
    if write:
        MODELS_DIR.mkdir(exist_ok=True)
        REPORTS_DIR.mkdir(exist_ok=True)
        joblib.dump({"model": final, "features": FEATURES, "threshold": thr}, MODELS_DIR / f"{model_id}.joblib")
        (REPORTS_DIR / f"{model_id}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        registry.register({"model_id": model_id, "data_kind": kind, "dataset_version": ds_version, "algorithm": chosen,
                           "metrics_test": test, "artifact": f"models/{model_id}.joblib", "report": f"reports/{model_id}.json"})
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["synthetic", "real"], default="synthetic")
    ap.add_argument("--students", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--data", type=Path)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    r = run(a.source, a.students, a.seed, a.data, quick=a.quick)
    print(json.dumps({k: r[k] for k in ("model_id", "data_kind", "dataset_version", "samples", "prevalence_test", "chosen", "threshold",
                                       "test", "test_ci95", "baselines_test", "error_by_grade_band")}, indent=2, ensure_ascii=False))
