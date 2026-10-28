# ruff: noqa: E402
import json

import pytest

pytest.importorskip("sklearn")

from app.core.config import get_settings
from tests.test_sync_reto10 import _ev, _login, _published, _pull, _push


def _closed_results(w, n_questions, n_correct_first=None):
    ta, tb, room, (st,) = _published(w, n_questions=n_questions)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    _push(w, sh, [_ev(t["student_assignment_id"], q["id"], 1, True, minutes=i) for i, q in enumerate(t["questions"])])
    return ta, tb, room, st


def _registry_with(tmp_path, monkeypatch, status):
    """Fixture de PRUEBA: entrena un modelo mínimo y SIMULA la aprobación humana escribiendo el registro."""
    from ml import predict, registry, train
    monkeypatch.setattr(registry, "REGISTRY_PATH", tmp_path / "reg.json")
    monkeypatch.setattr(train, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(train, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(predict, "MODELS_DIR", tmp_path / "models")
    train.run("synthetic", students=200, seed=3, quick=True)
    items = json.loads((tmp_path / "reg.json").read_text())
    items[0]["status"] = status
    if status == "APPROVED":
        # Simula metadatos de un modelo real aprobado; el artefacto sigue
        # siendo sintético y se usa exclusivamente en esta prueba aislada.
        items[0]["data_kind"] = "REAL"
    (tmp_path / "reg.json").write_text(json.dumps(items))


def test_forecast_unavailable_without_approved_model_and_system_keeps_working(w, tmp_path, monkeypatch):
    from ml import registry
    monkeypatch.setattr(registry, "REGISTRY_PATH", tmp_path / "empty.json")
    ta, _, room, _st = _closed_results(w, 12)
    r = w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast", headers=ta).json()
    assert r["available"] is False and "modelo aprobado" in r["reason"] and r["items"] == []
    assert w.c.get(f"/api/v1/analytics/classrooms/{room}/summary", headers=ta).status_code == 200   # el resto sigue


def test_candidate_model_is_not_used_by_default_and_is_labeled_when_explicitly_allowed(w, tmp_path, monkeypatch):
    _registry_with(tmp_path, monkeypatch, "CANDIDATE")
    ta, _, room, _st = _closed_results(w, 12)
    assert w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast", headers=ta).json()["available"] is False
    monkeypatch.setattr(get_settings(), "ml_allow_experimental", True)
    r = w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast", headers=ta).json()
    assert r["available"] is True and r["experimental"] is True and len(r["items"]) == 1
    it = r["items"][0]
    assert it["model_status"] == "CANDIDATE" and "EXPERIMENTAL" in it["warning"] and 0 <= it["probability"] <= 1
    assert it["difficulty_recommendation"]["source"] == "RULES"
    assert it["difficulty_recommendation"]["requires_teacher_decision"] is True


def test_approved_model_gives_advisory_probability_only_with_enough_evidence(w, tmp_path, monkeypatch):
    _registry_with(tmp_path, monkeypatch, "APPROVED")          # simula la aprobación humana (solo en pruebas)
    ta, _, room, _st = _closed_results(w, 12)
    r = w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast", headers=ta).json()
    assert r["available"] is True and r["experimental"] is False and len(r["items"]) == 1
    it = r["items"][0]
    assert it["model_status"] == "APPROVED" and it["warning"] is None and "No es un diagnóstico" in it["advisory"]
    assert it["probability"] < 0.5
    assert it["evidence_count"] >= 10
    assert it["difficulty_recommendation"]["source"] == "RULES"
    assert it["difficulty_recommendation"]["requires_teacher_decision"] is True
    assert it["difficulty_recommendation"]["action"] in {"LOWER", "MAINTAIN", "RAISE"}
    assert it["difficulty_recommendation"]["suggested_difficulty"] in {1, 2, 3}                              # 12 ejercicios resueltos sin ayuda: baja probabilidad de dificultad


def test_no_forecast_is_invented_with_fewer_than_10_closed_exercises(w, tmp_path, monkeypatch):
    _registry_with(tmp_path, monkeypatch, "APPROVED")
    ta, _, room, _st = _closed_results(w, 5)
    r = w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast", headers=ta).json()
    assert r["available"] is True and r["items"] == []


def test_forecast_access_control(w):
    ta, tb, room, st = _closed_results(w, 5)
    assert w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast", headers=tb).status_code == 404
    assert w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast").status_code == 401
    assert w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast", headers=_login(w, st)).status_code == 403


def test_inference_failure_uses_explicit_fallback(w, monkeypatch):
    from app.modules.forecast import service

    class BrokenPredictor:
        def load(self, **_kwargs):
            return {}, {}

        def predict(self, *_args, **_kwargs):
            raise ValueError("artifact incompatible")

    monkeypatch.setattr(service, "_load_predictor", lambda: BrokenPredictor())
    ta, _, room, _st = _closed_results(w, 12)
    response = w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast", headers=ta)
    assert response.status_code == 200
    assert response.json()["available"] is False
    assert "reglas" in response.json()["reason"]
    assert "artifact" not in response.text


def test_inference_receives_actual_wrong_attempts(w, monkeypatch):
    from app.modules.forecast import service

    captured = []

    class CapturingPredictor:
        def load(self, **_kwargs):
            return {}, {}

        def predict(self, hist, *_args, **_kwargs):
            captured.extend(hist)
            return {"status": "INSUFFICIENT_EVIDENCE"}

    monkeypatch.setattr(service, "_load_predictor", lambda: CapturingPredictor())
    ta, _, room, (st,) = _published(w, n_questions=1)
    sh = _login(w, st)
    task = _pull(w, sh)["tasks"][0]
    sa, qid = task["student_assignment_id"], task["questions"][0]["id"]
    _push(w, sh, [_ev(sa, qid, 1, False), _ev(sa, qid, 2, True)])
    assert w.c.get(f"/api/v1/analytics/classrooms/{room}/forecast", headers=ta).status_code == 200
    assert captured and captured[0]["wrong"] == 1
