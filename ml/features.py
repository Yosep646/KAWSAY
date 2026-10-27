import hashlib
import math

import numpy as np

from ml.common import FEATURES, FORBIDDEN_FEATURES, HISTORY, HORIZON, TARGET_MIN_DIFFICULT, adaptive

DIFF = adaptive.RULES["difficulty_score_max"]
assert not (set(FEATURES) & FORBIDDEN_FEATURES), "feature prohibida"


def _vec(hist: list[dict], grade: int) -> list[float]:
    s = np.array([r["score"] for r in hist], dtype=float)
    last5 = s[-5:]
    trend = float(np.polyfit(np.arange(len(s)), s, 1)[0]) if len(s) > 1 else 0.0
    return [s.mean(), last5.mean(), s.min(), s.std(), float((s <= DIFF).mean()), float((last5 <= DIFF).mean()),
            float(np.mean([r["hints"] for r in hist])), float(np.mean([r["wrong"] for r in hist])), trend,
            float(s[-3:].mean()), float(grade)]


def build_windows(sequences: list[dict]):
    """X (features del pasado), y (dificultad en los próximos 5), grupos (estudiante) y meta para auditoría."""
    validate_sequences(sequences)
    X, y, groups, meta = [], [], [], []
    for seq in sequences:
        res = seq["results"]
        for t in range(HISTORY, len(res) - HORIZON + 1):
            fut = res[t:t + HORIZON]
            X.append(_vec(res[t - HISTORY:t], seq["grade"]))
            y.append(int(sum(r["score"] <= DIFF for r in fut) >= TARGET_MIN_DIFFICULT))
            groups.append(seq["student"])
            last5 = res[t - 5:t]
            meta.append({"rule_flag": int(sum(r["score"] <= DIFF for r in last5) >= adaptive.RULES["support_min_difficult"]),
                         "grade": seq["grade"]})
    return np.array(X), np.array(y), np.array(groups), meta


def validate_sequences(sequences: list[dict]) -> None:
    """Rechaza datos inválidos y columnas personales inesperadas antes de entrenar.

    El identificador debe venir seudonimizado del exportador autorizado. La
    autorización y el orden cronológico son requisitos de procedencia externos.
    """
    if not isinstance(sequences, list) or not sequences:
        raise ValueError("Dataset vacío o formato inválido")
    for seq in sequences:
        if not isinstance(seq, dict) or set(seq) != {"student", "grade", "results"}:
            raise ValueError("Columnas de secuencia no permitidas")
        if not isinstance(seq["student"], str) or not seq["student"].strip():
            raise ValueError("Se requiere identificador seudonimizado")
        if type(seq["grade"]) is not int or not 1 <= seq["grade"] <= 6:
            raise ValueError("El modelo actual admite grados de primaria 1 a 6")
        if not isinstance(seq["results"], list):
            raise ValueError("Resultados inválidos")
        for r in seq["results"]:
            if not isinstance(r, dict) or not {"score", "hints", "wrong"} <= set(r) <= {"score", "hints", "wrong", "closed"}:
                raise ValueError("Columnas de resultado no permitidas")
            score = r["score"]
            if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError("Score debe ser finito y estar entre 0 y 1")
            if any(type(r[k]) is not int or not 0 <= r[k] <= 20 for k in ("hints", "wrong")):
                raise ValueError("Conteos de pistas/errores inválidos")
            if "closed" in r and r["closed"] is not True:
                raise ValueError("Solo se admiten ejercicios cerrados")


def dataset_version(X: np.ndarray, y: np.ndarray, params: dict) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(np.round(X, 6)).tobytes())
    h.update(y.tobytes())
    h.update(repr(sorted(params.items())).encode())
    return "ds-" + h.hexdigest()[:12]


def group_split(groups: np.ndarray, seed: int, fracs=(0.6, 0.2, 0.2)):
    """Partición POR ESTUDIANTE: ningún estudiante aparece en dos particiones (sin fuga de información)."""
    ids = np.array(sorted(set(groups.tolist())))
    rng = np.random.default_rng(seed)
    rng.shuffle(ids)
    n = len(ids)
    a, b = int(n * fracs[0]), int(n * (fracs[0] + fracs[1]))
    parts = {"train": set(ids[:a]), "val": set(ids[a:b]), "test": set(ids[b:])}
    return {k: np.array([g in v for g in groups]) for k, v in parts.items()}, parts
