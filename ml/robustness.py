"""Variabilidad entre semillas (datos y particiones distintos): ¿las conclusiones dependen de la suerte?
Uso: python -m ml.robustness --seeds 7 11 23 --students 1500   ->  ml/reports/robustness.json"""
import argparse
import json

import numpy as np

from ml import train
from ml.common import REPORTS_DIR


def main(seeds: list[int], students: int, quick: bool) -> dict:
    rows = []
    for s in seeds:
        r = train.run("synthetic", students, s, write=False, quick=quick)
        rows.append({"seed": s, "chosen": r["chosen"], "model": r["test"], "rule": r["baselines_test"]["regla_R-SUP-001_ultimos5"],
                     "heuristic": r["baselines_test"]["heuristica_media5<0.5"]})
    def agg(key: str, metric: str) -> dict:
        v = np.array([x[key][metric] for x in rows])
        return {"mean": round(float(v.mean()), 4), "std": round(float(v.std()), 4), "min": round(float(v.min()), 4), "max": round(float(v.max()), 4)}
    out = {"protocol": "grouped-calibration-v2", "seeds": seeds, "students": students, "runs": rows,
           "summary": {"model_f1": agg("model", "f1"), "model_roc_auc": agg("model", "roc_auc"), "model_pr_auc": agg("model", "pr_auc"),
                       "heuristic_f1": agg("heuristic", "f1"), "rule_f1": agg("rule", "f1"),
                       "f1_gain_over_heuristic": round(float(np.mean([x["model"]["f1"] - x["heuristic"]["f1"] for x in rows])), 4)}}
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "robustness.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[7, 11, 23])
    ap.add_argument("--students", type=int, default=1500)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    print(json.dumps(main(a.seeds, a.students, a.quick)["summary"], indent=2))
