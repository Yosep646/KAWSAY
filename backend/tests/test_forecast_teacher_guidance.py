"""Real teacher API: recommendations must work without an approved ML model."""
from app.modules.forecast import service as forecast_service
from tests.test_assignments import MC, _create, _env
from tests.test_sync_reto10 import _ev, _login, _pull, _push


def test_teacher_uses_real_learning_evidence_when_ml_is_unavailable(w, monkeypatch):
    _, teacher, other_teacher, room, topics = _env(w, grades=(4,))
    student = w.student(teacher, room, 4, "Alumno de cuarto")
    a = _create(w, teacher, room, topics, grades=(4,))
    variant = a["variants"][0]
    url = f"/api/v1/assignments/{a['id']}/variants/{variant['id']}"
    questions = [{**MC, "prompt": f"Suma comprobable número {n}"} for n in range(5)]
    assert w.c.put(url + "/questions", headers=teacher, json={"questions": questions}).status_code == 200
    assert w.c.post(url + "/approve", headers=teacher).status_code == 200
    assert w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=teacher).status_code == 200

    endpoint = f"/api/v1/analytics/classrooms/{room}/forecast"
    monkeypatch.setattr(forecast_service, "_load_predictor", lambda: None)
    empty = w.c.get(endpoint, headers=teacher)
    assert empty.status_code == 200
    assert empty.json()["available"] is False
    assert empty.json()["guidance"] == []
    assert empty.json()["items"] == []

    student_auth = _login(w, student)
    task = _pull(w, student_auth)["tasks"][0]
    for n, question in enumerate(task["questions"]):
        # Five genuinely submitted and server-evaluated answers.
        result = _push(w, student_auth, [_ev(task["student_assignment_id"], question["id"], 1, True, minutes=n)])
        assert result[0]["status"] == "ACKED"

    found = w.c.get(endpoint, headers=teacher)
    assert found.status_code == 200, found.text
    payload = found.json()
    assert payload["available"] is False and payload["items"] == []
    assert len(payload["guidance"]) == 1
    recommendation = payload["guidance"][0]
    assert recommendation["evidence_count"] == 5
    assert recommendation["action"] == "RAISE"
    assert recommendation["suggested_difficulty"] == 3
    assert recommendation["source"] == "RULES"
    assert recommendation["requires_teacher_decision"] is True
    assert "probability" not in recommendation
    assert "diagnosis" not in str(recommendation).lower()
    # Another institution cannot read students or learning support.
    assert w.c.get(endpoint, headers=other_teacher).status_code == 404
    assert w.c.get(endpoint, headers=student_auth).status_code == 403
