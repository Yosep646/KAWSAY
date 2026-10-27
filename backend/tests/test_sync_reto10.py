import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.modules.learning.models import LearningAttempt
from app.modules.support_flags.models import SupportFlag
from tests.test_assignments import _create, _env

DEV = "66666666-6666-6666-6666-666666666666"


def _q(i):
    return {"type": "MULTIPLE_CHOICE", "prompt": f"Pregunta {i}: ¿cuál es mayor?", "options": ["a", "b"],
            "correct_answer": {"index": 1}, "hints": ["pista 1", "pista 2"]}


def _published(w, n_questions=5, kids=(("Juan", 1),)):
    admin, ta, tb, room, topics = _env(w, grades=(1, 2))
    students = [w.student(ta, room, g, name) for name, g in kids]
    a = _create(w, ta, room, topics, grades=(1,))
    v = a["variants"][0]
    p = f"/api/v1/assignments/{a['id']}/variants/{v['id']}"
    assert w.c.put(p + "/questions", headers=ta, json={"questions": [_q(i) for i in range(n_questions)]}).status_code == 200
    assert w.c.post(p + "/approve", headers=ta).status_code == 200
    assert w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=ta).status_code == 200
    return ta, tb, room, students


def _login(w, st, dev=DEV):
    r = w.c.post("/api/v1/auth/student-login", json={"login_code": st["login_code"], "pin": st["pin"], "device_id": dev})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _pull(w, sh, cursor=0):
    r = w.c.get(f"/api/v1/sync/pull?cursor={cursor}", headers=sh)
    assert r.status_code == 200, r.text
    return r.json()


def _ev(sa_id, qid, n, correct, hints=0, minutes=0, claimed=None, eid=None):
    when = (datetime.now(UTC) - timedelta(hours=2) + timedelta(minutes=minutes)).isoformat()
    return {"event_id": eid or str(uuid.uuid4()), "type": "attempt.created", "payload": {
        "student_assignment_id": sa_id, "question_id": qid, "attempt_number": n,
        "answer": {"index": 1 if correct else 0}, "is_correct": correct if claimed is None else claimed,
        "hints_used": hints, "response_time_ms": 4000, "client_created_at": when}}


def _push(w, sh, events, dev=DEV):
    r = w.c.post("/api/v1/sync/push", headers=sh, json={"device_id": dev, "events": events})
    assert r.status_code == 200, r.text
    return r.json()["results"]


def test_pull_gives_offline_ready_task_with_answers_and_is_scoped_to_student(w):
    _, _, _, kids = _published(w, kids=(("Juan", 1), ("Ana", 1), ("Beto", 2)))
    j, ana, beto = (_login(w, k) for k in kids)
    pj = _pull(w, j)
    assert len(pj["tasks"]) == 1 and pj["has_more"] is False
    q = pj["tasks"][0]["questions"][0]
    assert q["correct_answer"] == {"index": 1} and q["hints"]            # lo necesario para trabajar offline
    assert _pull(w, beto)["tasks"] == []                                  # grado 2: sin variante
    assert _pull(w, j, cursor=pj["cursor"])["tasks"] == []                # incremental
    assert pj["tasks"][0]["student_assignment_id"] != _pull(w, ana)["tasks"][0]["student_assignment_id"]


def test_push_is_idempotent_no_duplicates(w, db):
    _, _, _, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    ev = _ev(t["student_assignment_id"], t["questions"][0]["id"], 1, True)
    assert _push(w, sh, [ev])[0]["status"] == "ACKED"
    assert _push(w, sh, [ev])[0]["status"] == "DUPLICATE"
    assert _push(w, sh, [ev, ev])[0]["status"] == "DUPLICATE"            # también dentro de un mismo lote
    assert db.query(LearningAttempt).count() == 1
    # mismo UUID desde otro dispositivo tampoco duplica
    assert _push(w, sh, [ev], dev="77777777-7777-7777-7777-777777777777")[0]["status"] == "DUPLICATE"
    assert db.query(LearningAttempt).count() == 1


def test_reused_event_id_with_changed_answer_is_conflict(w, db):
    _, _, _, (st,) = _published(w)
    sh = _login(w, st)
    task = _pull(w, sh)["tasks"][0]
    event = _ev(task["student_assignment_id"], task["questions"][0]["id"], 1, True)
    assert _push(w, sh, [event])[0]["status"] == "ACKED"
    changed = {**event, "payload": {**event["payload"], "answer": {"index": 0}}}
    assert _push(w, sh, [changed])[0] == {
        "event_id": event["event_id"], "status": "REJECTED", "reason": "event_id_conflict"}
    assert db.query(LearningAttempt).count() == 1


def test_student_can_resume_only_own_task_without_exposing_answers(w):
    _, _, _, (student, other) = _published(w, kids=(("Uno", 1), ("Dos", 1)))
    sh, other_sh = _login(w, student), _login(w, other)
    task = _pull(w, sh)["tasks"][0]
    event = _ev(task["student_assignment_id"], task["questions"][0]["id"], 1, True)
    assert _push(w, sh, [event])[0]["status"] == "ACKED"
    url = f"/api/v1/sync/tasks/{task['student_assignment_id']}/attempts?device_id={DEV}"
    response = w.c.get(url, headers=sh)
    assert response.status_code == 200
    assert response.json() == {"questions": [{"question_id": task["questions"][0]["id"], "closed": True, "device_attempt_number": 1}]}
    assert w.c.get(url, headers=other_sh).status_code == 404


def test_server_recorrects_and_validates_everything(w, db):
    _, _, _, (st, other) = _published(w, kids=(("Juan", 1), ("Otro", 1)))
    sh, osh = _login(w, st), _login(w, other, "88888888-8888-8888-8888-888888888888")
    t, ot = _pull(w, sh)["tasks"][0], _pull(w, osh)["tasks"][0]
    qid = t["questions"][0]["id"]
    # el cliente afirma "correcto" pero respondió mal: gana el servidor
    assert _push(w, sh, [_ev(t["student_assignment_id"], qid, 1, False, claimed=True)])[0]["status"] == "ACKED"
    a = db.query(LearningAttempt).one()
    assert a.is_correct is False and a.client_is_correct is True
    bad = _push(w, sh, [
        _ev(ot["student_assignment_id"], ot["questions"][0]["id"], 1, True),                     # tarea de OTRO alumno
        _ev(t["student_assignment_id"], str(uuid.uuid4()), 1, True),                             # pregunta inexistente
        _ev(t["student_assignment_id"], qid, 1, True, eid=str(uuid.uuid4())),                    # attempt_number repetido
        {"event_id": str(uuid.uuid4()), "type": "algo.raro", "payload": {}},
        {"event_id": str(uuid.uuid4()), "type": "attempt.created", "payload": {"x": 1}},
        {"event_id": "no-es-uuid", "type": "attempt.created", "payload": {}},
    ])
    assert [r["status"] for r in bad] == ["REJECTED"] * 6
    assert [r.get("reason") for r in bad][:5] == ["student_assignment_not_found", "question_not_in_assignment",
                                                    "duplicate_or_conflict", "unsupported_event_type", "invalid_payload"]
    assert db.query(LearningAttempt).count() == 1
    # un rechazo es determinista al reenviar el mismo UUID
    again = _push(w, sh, [{"event_id": bad[3]["event_id"], "type": "algo.raro", "payload": {}}])
    assert again[0]["status"] == "REJECTED"


def test_future_client_clock_cannot_inflate_time(w, db):
    _, _, _, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    ev = _ev(t["student_assignment_id"], t["questions"][0]["id"], 1, True, minutes=60 * 24 * 5)   # +5 días
    assert _push(w, sh, [ev])[0]["status"] == "ACKED"
    a = db.query(LearningAttempt).one()
    assert a.effective_at <= a.received_at


def test_attempts_are_append_only_in_db(w, db):
    _, _, _, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    _push(w, sh, [_ev(t["student_assignment_id"], t["questions"][0]["id"], 1, True)])
    with pytest.raises(DBAPIError):
        db.execute(text("UPDATE learning_attempts SET is_correct = NOT is_correct"))
    db.rollback()
    with pytest.raises(DBAPIError):
        db.execute(text("DELETE FROM learning_attempts"))
    db.rollback()


def _struggle(w, sh, t, difficult_questions=4):
    """4 ejercicios con dificultad (6 pistas en total) + 1 resuelto sin ayuda."""
    qs = [q["id"] for q in t["questions"]]
    sa = t["student_assignment_id"]
    ev, m = [], 0
    plan = {0: [(False, 1), (False, 1), (False, 0)],      # 2 pistas
            1: [(False, 1), (False, 1), (False, 0)],      # 2 pistas
            2: [(False, 0), (False, 1), (True, 1)],       # correcto tras 2 pistas y 2 errores => 0.4
            4: [(False, 0), (False, 0), (False, 0)]}      # 0 pistas
    for qi, steps in list(plan.items())[:difficult_questions]:
        for n, (ok, hints) in enumerate(steps, start=1):
            ev.append(_ev(sa, qs[qi], n, ok, hints, minutes=m))
            m += 1
    ev.append(_ev(sa, qs[3], 1, True, 0, minutes=m))
    return ev


def test_reto10_pattern_becomes_explainable_support_flag_on_teacher_dashboard(w, db):
    ta, tb, room, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    events = _struggle(w, sh, t)
    assert all(r["status"] == "ACKED" for r in _push(w, sh, events))
    assert all(r["status"] == "DUPLICATE" for r in _push(w, sh, events))        # reenviar todo: sin flags nuevos
    assert db.query(SupportFlag).count() == 1

    flags = w.c.get(f"/api/v1/support-flags?classroom_id={room}", headers=ta).json()
    assert len(flags) == 1
    f = flags[0]
    assert f["status"] == "OPEN" and f["student"]["display_name"] == "Juan" and f["student"]["grade"] == "1.º PRIMARIA"
    assert f["competency"]["name"].startswith("Resuelve problemas de cantidad")
    ev = f["evidence"]
    assert (ev["difficult"], ev["window"], ev["hints_total"]) == (4, 5, 6)
    assert ev["topics"] == ["Tema grado 1"] and len(ev["results"]) == 5
    assert "4 de los últimos 5 ejercicios" in f["message"] and "6 pistas" in f["message"]
    assert f["rule_id"] == "R-SUP-001" and "diagn" not in f["message"].lower()

    # el resumen del dashboard refleja datos reales
    summ = w.c.get(f"/api/v1/analytics/classrooms/{room}/summary", headers=ta).json()
    assert summ["students_total"] == 1 and summ["open_support_flags"] == 1 and summ["students_with_activity"] == 1
    assert summ["attempts_total"] == len(events) and summ["published_assignments"] == 1
    prog = w.c.get(f"/api/v1/analytics/classrooms/{room}/students/{st['id']}/progress", headers=ta).json()
    c = prog["competencies"][0]
    assert c["score"] is not None and c["score"] < 0.5 and c["state"] == "REFUERZO" and c["evidence_count"] == 5
    recommendation = c["difficulty_recommendation"]
    assert recommendation["action"] == "LOWER" and recommendation["suggested_difficulty"] == 1
    assert recommendation["source"] == "RULES" and recommendation["requires_teacher_decision"] is True

    # intervención + evolución observada (sin causalidad)
    comp_id = f["competency"]["id"]
    iv = w.c.post("/api/v1/interventions", headers=ta, json={
        "student_id": st["id"], "competency_id": comp_id, "strategy": "Actividad guiada con material concreto",
        "support_flag_id": f["id"]})
    assert iv.status_code == 201
    assert w.c.get("/api/v1/support-flags?status=ACKNOWLEDGED", headers=ta).json()[0]["id"] == f["id"]
    listed = w.c.get(f"/api/v1/interventions?student_id={st['id']}", headers=ta).json()[0]
    assert listed["score_at_creation"] == c["score"] and "causa" in listed["note"]
    assert w.c.patch(f"/api/v1/support-flags/{f['id']}", headers=ta, json={"status": "RESOLVED"}).json()["status"] == "RESOLVED"

    # otro docente no ve nada de este alumno
    assert w.c.get("/api/v1/support-flags", headers=tb).json() == []
    assert w.c.patch(f"/api/v1/support-flags/{f['id']}", headers=tb, json={"status": "DISMISSED"}).status_code == 404
    assert w.c.get(f"/api/v1/interventions?student_id={st['id']}", headers=tb).status_code == 404
    assert w.c.get(f"/api/v1/analytics/classrooms/{room}/summary", headers=tb).status_code == 404
    # alumno: sin acceso a alertas; su progreso es positivo y sencillo
    assert w.c.get("/api/v1/support-flags", headers=sh).status_code == 403
    mine = w.c.get("/api/v1/progress/me", headers=sh).json()
    assert mine and set(mine[0]) == {"competency", "percent"}


def test_no_flag_with_3_of_5_or_open_questions_and_no_percent_without_evidence(w, db):
    ta, _, room, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    qs = [q["id"] for q in t["questions"]]
    ev = []
    for qi in range(3):                                      # 3 con dificultad
        ev += [_ev(t["student_assignment_id"], qs[qi], n, False, 1, minutes=qi * 3 + n) for n in (1, 2, 3)]
    ev += [_ev(t["student_assignment_id"], qs[3], 1, True, minutes=30), _ev(t["student_assignment_id"], qs[4], 1, True, minutes=31)]
    assert all(r["status"] == "ACKED" for r in _push(w, sh, ev))
    assert db.query(SupportFlag).count() == 0
    mine = w.c.get("/api/v1/progress/me", headers=sh).json()
    assert mine[0]["percent"] is not None                    # 5 ejercicios cerrados => hay porcentaje


def test_percentage_is_null_without_enough_evidence(w):
    _, _, room, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    r = _push(w, sh, [_ev(t["student_assignment_id"], t["questions"][0]["id"], 1, True)])
    assert r[0]["status"] == "ACKED"
    assert w.c.get("/api/v1/progress/me", headers=sh).json()[0]["percent"] is None   # 1 ejercicio: sin inventar %


def test_sync_endpoints_require_student_role(w):
    ta, _, _, (st,) = _published(w)
    sh = _login(w, st)
    assert w.c.post("/api/v1/sync/push", headers=ta, json={"device_id": DEV, "events": []}).status_code in (403, 422)
    assert w.c.get("/api/v1/sync/pull", headers=ta).status_code == 403
    assert w.c.get("/api/v1/sync/pull").status_code == 401
    assert w.c.post("/api/v1/sync/push", headers=sh, json={"device_id": DEV, "events": []}).status_code == 422
    assert w.c.post("/api/v1/sync/push", headers=sh, json={"device_id": DEV, "events": [
        {"event_id": str(uuid.uuid4()), "type": "attempt.created"} for _ in range(101)]}).status_code == 422
