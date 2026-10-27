"""Inferencia SEPARADA del entrenamiento. Solo carga modelos APPROVED (revisión humana)."""
import joblib
import numpy as np

from ml import registry
from ml.common import FEATURES, MODELS_DIR
from ml.features import _vec


class NoApprovedModel(Exception):
    pass


def load(allow_experimental: bool = False) -> tuple[dict, dict]:
    items = registry.list_models()
    # El registro puede haber sido editado o proceder de una versión anterior:
    # nunca tratar un artefacto sintético como aprobado para producción.
    approved = [m for m in items if m.get("status") == "APPROVED" and m.get("data_kind") == "REAL"]
    pool = approved or ([m for m in items if m["status"] == "CANDIDATE"] if allow_experimental else [])
    if not pool:
        raise NoApprovedModel("No hay ningún modelo APPROVED. El sistema usa solo las reglas auditables.")
    meta = pool[-1]
    return joblib.load(MODELS_DIR / f"{meta['model_id']}.joblib"), meta


def predict(history: list[dict], grade: int, allow_experimental: bool = False) -> dict:
    if len(history) < 10:
        return {"status": "INSUFFICIENT_EVIDENCE", "probability": None}
    bundle, meta = load(allow_experimental)
    x = np.array([_vec(history[-10:], grade)])
    assert bundle["features"] == FEATURES
    p = float(bundle["model"].predict_proba(x)[0, 1])
    return {"status": "OK", "probability": round(p, 4), "above_threshold": p >= bundle["threshold"],
            "model_id": meta["model_id"], "model_status": meta["status"], "data_kind": meta["data_kind"],
            "warning": None if meta["status"] == "APPROVED" else "EXPERIMENTAL: entrenado con datos sintéticos; no usar para decidir."}
