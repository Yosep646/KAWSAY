"""Pronóstico de dificultad con ML (OPCIONAL). El backend NO depende de scikit-learn ni del paquete `ml/`:
si no están, o si no hay un modelo APROBADO por una persona, se informa y todo lo demás sigue con reglas auditables."""
import importlib
import sys
import uuid
from pathlib import Path
from time import perf_counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain import adaptive
from app.modules.curriculum.models import Competency
from app.modules.learning.models import LearningAttempt

REPO_ROOT = Path(__file__).resolve().parents[4]
ADVISORY = "Señal de apoyo para el docente. No es un diagnóstico ni decide por sí sola."


def _load_predictor() -> Any | None:
    try:
        if (REPO_ROOT / "ml").is_dir() and str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        return importlib.import_module("ml.predict")
    except Exception:
        return None


def forecast_for_students(db: Session, students: dict[uuid.UUID, dict]) -> dict:
    pred = _load_predictor()
    if pred is None:
        return {"available": False, "reason": "El módulo de ML no está instalado en este servidor (es opcional).", "items": []}
    allow = get_settings().ml_allow_experimental
    try:
        pred.load(allow_experimental=allow)
    except Exception:
        return {"available": False, "items": [],
                "reason": "No hay ningún modelo aprobado por una persona. Se usan solo las alertas por reglas."}
    names = {c.id: c.name for c in db.scalars(select(Competency))}
    by_key: dict[tuple, list] = {}
    for a in db.scalars(select(LearningAttempt).where(LearningAttempt.student_user_id.in_(list(students)))):
        by_key.setdefault((a.student_user_id, a.competency_id), []).append(adaptive.AttemptFact(
            str(a.id), str(a.question_id), a.attempt_number, a.is_correct, a.hints_used, a.effective_at))
    items = []
    for (sid, cid), facts in by_key.items():
        results = sorted((r for r in adaptive.question_results(facts) if r.closed), key=lambda r: r.at)
        hist = [{"score": r.score, "hints": r.hints, "wrong": r.wrong_attempts} for r in results]
        progress_score, evidence_count = adaptive.compute_progress(results)
        support = adaptive.difficulty_recommendation(progress_score, evidence_count)
        started = perf_counter()
        try:
            out = pred.predict(hist, students[sid]["grade_number"], allow_experimental=allow)
        except Exception:
            return {"available": False, "items": [],
                    "reason": "La inferencia no está disponible. Se mantienen las alertas por reglas."}
        inference_ms = round((perf_counter() - started) * 1000, 3)
        if out.get("status") != "OK":
            continue
        items.append({"student": {"id": sid, "display_name": students[sid]["display_name"]},
                      "competency": {"id": cid, "name": names.get(cid)}, "probability": out["probability"],
                      "above_threshold": out["above_threshold"], "model_id": out["model_id"], "model_status": out["model_status"],
                      "warning": out["warning"], "advisory": ADVISORY, "inference_ms": inference_ms,
                      "evidence_count": evidence_count,
                      "difficulty_recommendation": {
                          **support,
                          "source": "RULES",
                          "method_version": adaptive.METHOD_VERSION,
                          "requires_teacher_decision": True,
                      }})
    items.sort(key=lambda x: -x["probability"])
    return {"available": True, "experimental": bool(items and items[0]["model_status"] != "APPROVED"), "items": items}
