"""Tutor: datos reales, pista progresiva y señal de automatización deduplicada."""
import uuid

import httpx

from app.modules.automation import dispatch
from app.modules.automation.models import DomainEvent
from tests.test_automation_languages_tutor import _cfg
from tests.test_sync_reto10 import _login, _published, _pull


def test_repeated_tutor_help_emits_one_minimal_signed_outbox_event(w, db, monkeypatch):
    _cfg(monkeypatch)
    teacher, _, _, (student,) = _published(w)
    auth = _login(w, student)
    task = _pull(w, auth)["tasks"][0]
    question = task["questions"][0]
    req = {"student_assignment_id": task["student_assignment_id"],
           "question_id": question["id"], "step": 2}
    for _ in range(3):
        response = w.c.post("/api/v1/tutor/turn", headers=auth, json=req)
        assert response.status_code == 200
        assert response.json()["source"] == "RULES"
        assert response.json()["answer_revealed"] is False

    events = db.query(DomainEvent).filter_by(type="tutor.help.requested").all()
    assert len(events) == 1
    ev = events[0]
    assert ev.id == uuid.uuid5(uuid.NAMESPACE_URL,
                               f"kawsay:tutor:help:{task['student_assignment_id']}:{question['id']}")
    assert set(ev.payload) == {"student_id", "assignment_id", "teacher_id", "classroom_id",
                               "question_id", "min_help_step"}
    assert ev.status == "PENDING"
    assert student["display_name"] not in str(ev.payload)

    received = []
    def receiver(request: httpx.Request) -> httpx.Response:
        received.append(request)
        return httpx.Response(200, json={"ok": True})

    result = dispatch.dispatch_pending(db, httpx.Client(transport=httpx.MockTransport(receiver)))
    assert result["delivered"] >= 1
    msg = next(x for x in received if "tutor.help.requested" in x.content.decode())
    assert "student_id" not in msg.content.decode()  # seudónimo interno no sale a n8n
    assert "question_id" not in msg.content.decode()
    assert dispatch.verify("secreto-compartido-n8n-0123456789",
                           msg.headers["X-Kawsay-Timestamp"], msg.content.decode(),
                           msg.headers["X-Kawsay-Signature"])


def test_first_hint_does_not_generate_intervention_automatically(w, db):
    _, _, _, (student,) = _published(w)
    task = _pull(w, _login(w, student))["tasks"][0]
    response = w.c.post("/api/v1/tutor/turn", headers=_login(w, student), json={
        "student_assignment_id": task["student_assignment_id"],
        "question_id": task["questions"][0]["id"], "step": 1,
    })
    assert response.status_code == 200
    assert db.query(DomainEvent).filter_by(type="tutor.help.requested").count() == 0
