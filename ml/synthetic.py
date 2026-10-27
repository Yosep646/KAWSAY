"""Simulador de estudiantes (SINTÉTICO). No son datos reales; sirve solo para probar el pipeline.

Modelo generativo (independiente de la regla R-SUP-001): capacidad latente con crecimiento, rachas de bajón,
dificultad de ejercicio y uso de pistas. Los intentos simulados pasan por las funciones de producción
para obtener el mismo `score` que tendría el sistema real.
"""
from datetime import datetime, timedelta, timezone

import numpy as np

from ml.common import adaptive

DATA_KIND = "SYNTHETIC"


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def simulate_sequences(n_students: int, seed: int, n_results: int = 30) -> list[dict]:
    rng = np.random.default_rng(seed)
    base = datetime(2026, 3, 2, 9, tzinfo=timezone.utc)
    out = []
    for i in range(n_students):
        grade = int(rng.integers(1, 7))
        theta0, growth = rng.normal(0, 1), rng.normal(0.03, 0.04)
        slump_start = int(rng.integers(5, n_results - 6)) if rng.random() < 0.3 else None
        d_student = rng.normal(0, 0.5)
        facts, qres = [], []
        for t in range(n_results):
            theta = theta0 + growth * t - (1.6 if slump_start is not None and slump_start <= t < slump_start + 8 else 0)
            d = d_student + rng.normal(0, 0.4)
            hints_total, a = 0, 0
            while a < 3:
                a += 1
                use_hint = rng.random() < 0.8 * _sigmoid(-(theta - d))
                hints = int(use_hint)
                hints_total += hints
                p = _sigmoid(1.3 * (theta - d) + 0.5 * hints_total)
                ok = bool(rng.random() < p)
                facts.append(adaptive.AttemptFact(f"{i}-{t}-{a}", f"{i}-{t}", a, ok, hints,
                                                  base + timedelta(days=t // 3, minutes=t * 7 + a)))
                if ok:
                    break
        for r in sorted(adaptive.question_results(facts), key=lambda r: r.at):
            qres.append({"score": r.score, "hints": r.hints, "wrong": r.wrong_attempts, "closed": r.closed})
        out.append({"student": f"S{i:05d}", "grade": grade, "results": [q for q in qres if q["closed"]]})
    return out
