import json
import time
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.core.config import get_settings
from app.domain import adaptive as A
from app.modules.audit.models import AuditLog
from app.modules.automation import dispatch
from app.modules.automation.models import DomainEvent
from tests.fakes import FakeProvider, install
from tests.test_sync_reto10 import _ev, _login, _published, _pull, _push, _struggle

SECRET = "secreto-compartido-n8n-0123456789"


@pytest.mark.parametrize("timestamp", ["nan", "inf", "-inf", "invalid", ""])
def test_webhook_verification_rejects_invalid_timestamp(timestamp):
    body = '{}'
    signature = dispatch.sign(SECRET, timestamp, body)
    assert not dispatch.verify(SECRET, timestamp, body, signature)


def _cfg(monkeypatch, url="http://n8n.local/webhook/kawsay"):
    s = get_settings()
    monkeypatch.setattr(s, "automation_webhook_url", url)
    monkeypatch.setattr(s, "automation_webhook_secret", SECRET)


def _flag_scenario(w):
    ta, tb, room, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    _push(w, sh, _struggle(w, sh, t))
    return ta, tb, room, st, sh, t


# ------------------------------------------------------------------ n8n / outbox
def test_support_flag_emits_minimal_event_and_n8n_receives_signed_webhook(w, db, monkeypatch):
    _cfg(monkeypatch)
    _flag_scenario(w)
    ev = db.query(DomainEvent).filter_by(type="student.support_flag.created").one()
    assert ev.status == "PENDING" and set(ev.payload) == {"flag_id", "rule_id", "competency_id", "classroom_ids", "teacher_ids"}
    assert "Juan" not in json.dumps(ev.payload)                              # sin nombres de estudiantes hacia n8n
    got = []

    def receiver(req: httpx.Request) -> httpx.Response:
        got.append(req)
        return httpx.Response(200, json={"ok": True})

    res = dispatch.dispatch_pending(db, httpx.Client(transport=httpx.MockTransport(receiver)))
    assert res["delivered"] >= 1
    r = next(x for x in got if json.loads(x.content)["type"] == "student.support_flag.created")
    body, ts, sig = r.content.decode(), r.headers["X-Kawsay-Timestamp"], r.headers["X-Kawsay-Signature"]
    assert dispatch.verify(SECRET, ts, body, sig)                            # el receptor puede verificar la firma
    assert not dispatch.verify(SECRET, ts, body + " ", sig) and not dispatch.verify("otro-secreto", ts, body, sig)
    assert not dispatch.verify(SECRET, str(time.time() - 3600), body, dispatch.sign(SECRET, str(time.time() - 3600), body))
    db.expire_all()
    assert db.get(DomainEvent, ev.id).status == "DELIVERED"


def test_n8n_down_does_not_break_core_and_events_retry_with_backoff(w, db, monkeypatch):
    _cfg(monkeypatch)
    ta, _, room, st, sh, t = _flag_scenario(w)

    def down(_req):
        raise httpx.ConnectError("n8n caído")

    res = dispatch.dispatch_pending(db, httpx.Client(transport=httpx.MockTransport(down)))
    assert res["delivered"] == 0 and res["retry_later"] >= 1
    ev = db.query(DomainEvent).filter_by(type="student.support_flag.created").one()
    assert ev.status == "PENDING" and ev.attempts == 1 and ev.last_error == "ConnectError"
    assert ev.next_attempt_at > datetime.now(UTC) + timedelta(seconds=20)    # backoff: no reintenta de inmediato
    # el núcleo sigue: alerta visible, dashboard, login y sync funcionan
    assert len(w.c.get(f"/api/v1/support-flags?classroom_id={room}", headers=ta).json()) == 1
    assert w.c.get(f"/api/v1/analytics/classrooms/{room}/summary", headers=ta).status_code == 200
    assert _pull(w, sh)["tasks"]
    # reintento inmediato: aún no vence => no se vuelve a llamar
    assert dispatch.dispatch_pending(db, httpx.Client(transport=httpx.MockTransport(down)))["retry_later"] == 0
    # 5xx también se reintenta; tras MAX intentos pasa a FAILED
    ev.attempts, ev.next_attempt_at = dispatch.MAX_ATTEMPTS - 1, datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    dispatch.dispatch_pending(db, httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503))))
    db.expire_all()
    assert db.get(DomainEvent, ev.id).status == "FAILED"


def test_dispatch_is_disabled_without_config_and_admin_only(w, db, monkeypatch):
    ta, *_ = _flag_scenario(w)
    assert dispatch.dispatch_pending(db)["status"] == "disabled"
    assert w.c.post("/api/v1/automation/dispatch", headers=ta).status_code == 403
    assert w.c.get("/api/v1/automation/events", headers=ta).status_code == 403
    admin = w.login("admin@x.pe")
    types = {e["type"] for e in w.c.get("/api/v1/automation/events", headers=admin).json()}
    assert {"student.support_flag.created", "sync.completed"} <= types


def test_admin_can_retry_failed_events_without_replaying_delivered_ones(w, db):
    teacher, *_ = _flag_scenario(w)
    event = db.query(DomainEvent).filter_by(type="student.support_flag.created").one()
    event.status, event.attempts, event.last_error = "FAILED", 8, "http_503"
    db.commit()
    url = f"/api/v1/automation/events/{event.id}/retry"
    assert w.c.post(url, headers=teacher).status_code == 403
    admin = w.login("admin@x.pe")
    assert w.c.post(url, headers=admin).json()["status"] == "PENDING"
    db.expire_all()
    assert event.attempts == 0 and event.last_error is None
    assert db.query(AuditLog).filter_by(action="automation.event.retry", target_id=event.id).count() == 1
    assert w.c.post(url, headers=admin).status_code == 409
    event.status = "DELIVERED"
    db.commit()
    assert w.c.post(url, headers=admin).status_code == 409
    assert w.c.post(f"/api/v1/automation/events/{uuid.uuid4()}/retry", headers=admin).status_code == 404


def test_assignment_published_event(w, db):
    _published(w)
    ev = db.query(DomainEvent).filter_by(type="assignment.published").one()
    assert ev.payload["students_assigned"] == 1 and set(ev.payload) == {"assignment_id", "classroom_id", "teacher_id", "students_assigned"}


# ------------------------------------------------------------------ idiomas y traducciones verificadas
def _approved_variant(w):
    ta, tb, room, (st,) = _published(w)
    a = w.c.get("/api/v1/assignments", headers=ta).json()[0]
    det = w.c.get(f"/api/v1/assignments/{a['id']}", headers=ta).json()
    return ta, st, a["id"], det["variants"][0]


def test_languages_are_declared_never_inferred_and_variants_validated(w, db):
    ta, st, *_ = _approved_variant(w)
    sh = _login(w, st)
    assert w.c.get("/api/v1/students/me/languages", headers=sh).json() == {
        "mother_language": None, "mother_variant_id": None, "preferred_language": None}   # nada por ubicación/escuela
    langs = {x["code"]: x for x in w.c.get("/api/v1/languages", headers=sh).json()}
    assert set(langs) == {"es", "qu", "ay"} and langs["qu"]["variants"] == []             # sin variantes inventadas
    admin = w.login("admin@x.pe")
    v = w.c.post("/api/v1/languages/variants", headers=admin, json={"language_code": "qu", "code": "qu-demo", "name": "Quechua (variante DEMO)"})
    assert v.status_code == 201 and w.c.post("/api/v1/languages/variants", headers=ta, json={
        "language_code": "qu", "code": "x2", "name": "no admin"}).status_code == 403
    ok = w.c.put("/api/v1/students/me/languages", headers=sh, json={
        "mother_language_code": "qu", "mother_variant_id": v.json()["id"], "preferred_language_code": "es"})
    assert ok.status_code == 200 and ok.json()["mother_language"] == "qu" and ok.json()["preferred_language"] == "es"
    bad = w.c.put("/api/v1/students/me/languages", headers=sh, json={
        "mother_language_code": "ay", "mother_variant_id": v.json()["id"]})                # variante de quechua con aimara
    assert bad.status_code == 409
    assert w.c.put("/api/v1/students/me/languages", headers=sh, json={"mother_language_code": "xx"}).status_code == 404
    # el docente puede declararlo por su estudiante; otro docente no
    assert w.c.put(f"/api/v1/students/{st['id']}/languages", headers=ta, json={"preferred_language_code": "qu"}).status_code == 200
    declared = w.c.get(f"/api/v1/students/{st['id']}/languages", headers=ta)
    assert declared.status_code == 200 and declared.json() == {
        "mother_language": None, "mother_variant_id": None, "preferred_language": "qu"}
    assert w.c.get(f"/api/v1/students/{st['id']}/languages", headers=w.login("tb@x.pe")).status_code == 404
    db.expire_all()
    assert db.query(AuditLog).filter_by(action="students.languages.read", target_id=uuid.UUID(st["id"])).count() == 1


def test_language_change_is_available_to_incremental_sync(w):
    ta, st, *_ = _approved_variant(w)
    sh = _login(w, st)
    first = _pull(w, sh)
    assert first["tasks"]
    changed = w.c.put(f"/api/v1/students/{st['id']}/languages", headers=ta, json={
        "mother_language_code": None, "mother_variant_id": None, "preferred_language_code": "qu"})
    assert changed.status_code == 200
    refreshed = _pull(w, sh, first["cursor"])
    assert refreshed["tasks"] and all(task["language"]["preferred"] == "qu" for task in refreshed["tasks"])


def test_only_verified_human_translations_reach_the_student(w):
    ta, st, aid, var = _approved_variant(w)
    admin, sh = w.login("admin@x.pe"), _login(w, st)
    base = f"/api/v1/assignments/{aid}/variants/{var['id']}/translations"
    qid = var["questions"][0]["id"]
    payload = {"language_code": "qu", "title": "Título (texto DEMO escrito por una persona)",
               "instructions": "Instrucciones traducidas DEMO por una persona", "question_prompts": {qid: "Pregunta DEMO traducida"}}
    w.c.put(f"/api/v1/students/{st['id']}/languages", headers=ta, json={"preferred_language_code": "qu"})
    # sin traducción: el estudiante recibe el contenido base y la app sabe que no hay traducción (no se inventa)
    t0 = _pull(w, sh)["tasks"][0]
    assert t0["translation"] is None and t0["language"] == {"preferred": "qu", "translation_available": False}
    assert w.c.post(base, headers=ta, json={**payload, "language_code": "es"}).status_code == 409
    assert w.c.post(base, headers=ta, json={**payload, "question_prompts": {str(uuid.uuid4()): "x"}}).status_code == 409
    tr = w.c.post(base, headers=ta, json=payload)
    assert tr.status_code == 201 and tr.json()["status"] == "DRAFT"
    tid = tr.json()["id"]
    assert _pull(w, sh)["tasks"][0]["translation"] is None                              # borrador: no se entrega
    assert w.c.post(f"/api/v1/translations/{tid}/verify", headers=admin).status_code == 409   # aún no está en revisión
    assert w.c.post(f"/api/v1/translations/{tid}/submit", headers=ta).status_code == 200
    assert w.c.post(f"/api/v1/translations/{tid}/verify", headers=ta).status_code == 403      # el docente no verifica
    assert _pull(w, sh)["tasks"][0]["translation"] is None                              # en revisión: tampoco
    assert w.c.post(f"/api/v1/translations/{tid}/verify", headers=admin).status_code == 200
    got = _pull(w, sh)["tasks"][0]
    assert got["translation"]["language"] == "qu" and got["translation"]["question_prompts"] == {qid: "Pregunta DEMO traducida"}
    assert got["language"]["translation_available"] is True
    # un estudiante con español preferido no recibe traducción
    w.c.put("/api/v1/students/me/languages", headers=sh, json={"preferred_language_code": "es"})
    assert _pull(w, sh)["tasks"][0]["translation"] is None
    # modificar la traducción exige nueva verificación
    w.c.put("/api/v1/students/me/languages", headers=sh, json={"preferred_language_code": "qu"})
    w.c.post(base, headers=ta, json={**payload, "title": "Título corregido"})
    assert _pull(w, sh)["tasks"][0]["translation"] is None


# ------------------------------------------------------------------ tutor
def test_tutor_guides_without_revealing_the_answer(w):
    ta, tb, room, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    sa, q = t["student_assignment_id"], t["questions"][0]
    body = {"student_assignment_id": sa, "question_id": q["id"]}
    s0 = w.c.post("/api/v1/tutor/turn", headers=sh, json=body).json()
    assert s0["step"] == 0 and s0["source"] == "RULES" and not s0["answer_revealed"] and "léelo" in s0["message"].lower()
    _push(w, sh, [_ev(sa, q["id"], 1, False, 1)])                                       # un error
    s1 = w.c.post("/api/v1/tutor/turn", headers=sh, json=body).json()
    assert s1["step"] == 1 and s1["message"] == "pista 1" and not s1["answer_revealed"]    # pista del docente
    _push(w, sh, [_ev(sa, q["id"], 2, False, 1, minutes=1)])
    assert w.c.post("/api/v1/tutor/turn", headers=sh, json=body).json()["message"] == "pista 2"
    _push(w, sh, [_ev(sa, q["id"], 3, False, 0, minutes=2)])                            # 3 intentos: ejercicio cerrado
    end = w.c.post("/api/v1/tutor/turn", headers=sh, json=body).json()
    assert end["closed"] and end["answer_revealed"]
    # propiedad: otro alumno / docente no pueden usar el tutor sobre esta tarea
    assert w.c.post("/api/v1/tutor/turn", headers=ta, json=body).status_code == 403
    assert w.c.post("/api/v1/tutor/turn", headers=sh, json={**body, "student_assignment_id": str(uuid.uuid4())}).status_code == 404


def test_tutor_ai_hint_is_validated_and_never_receives_the_answer(w):
    _, _, _, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    sa, q = t["student_assignment_id"], t["questions"][0]
    _push(w, sh, [_ev(sa, q["id"], 1, False, 1)])
    body = {"student_assignment_id": sa, "question_id": q["id"]}
    fake = FakeProvider(lambda r: "Piensa qué opción tiene más: compara con calma las dos.")
    install(w.app, fake)
    r = w.c.post("/api/v1/tutor/turn", headers=sh, json=body).json()
    assert r["source"] == "AI" and "compara" in r["message"]
    assert "correct" not in fake.calls[0].user.lower() and "index" not in fake.calls[0].user.lower()
    # la IA filtra la respuesta, mete un enlace, o cae: se usa la pista de reglas
    for bad in (lambda r: "La respuesta correcta es b", lambda r: "Mira b que es la correcta", lambda r: "Entra a https://x.example"):
        install(w.app, FakeProvider(bad))
        out = w.c.post("/api/v1/tutor/turn", headers=sh, json=body).json()
        assert out["source"] == "RULES" and out["message"] == "pista 1"
    from app.modules.ai.gateway import AIUnavailable
    from tests.fakes import raising
    install(w.app, FakeProvider(raising(AIUnavailable("x"))))
    assert w.c.post("/api/v1/tutor/turn", headers=sh, json=body).json()["source"] == "RULES"


# ------------------------------------------------------------------ fortalezas, motivación, auditoría
def _r(i, score, hints, day=0):
    return A.QuestionResult(f"q{i}", score, score > 0, True, 1, 0, hints, datetime(2026, 5, 4 + day, 9, i, tzinfo=UTC))


def test_strengths_and_motivation_are_evidence_based():
    improving = [_r(i, 0.4, 2) for i in range(5)] + [_r(5 + i, 1.0, 0) for i in range(5)]
    names = {s["rule_id"] for s in A.detect_strengths(improving)}
    assert {"S-HINTS-001", "S-IMPROVE-001", "S-STREAK-001"} <= names
    assert A.detect_strengths([_r(i, 0.4, 2) for i in range(10)]) == []                  # sin mejora: sin "fortaleza"
    assert A.detect_strengths([_r(i, 1.0, 0) for i in range(2)]) == []                   # poca evidencia
    assert A.motivation_messages([], "X") == []
    two_days = [_r(i, 0.7, 2, day=0) for i in range(3)] + [_r(3 + i, 0.7, 1, day=1) for i in range(3)]
    msg = A.motivation_messages(two_days, "Cantidad")
    assert any("menos pistas" in m and "1.0 frente a 2.0" in m for m in msg)
    streak = A.motivation_messages([_r(i, 1.0, 0) for i in range(4)], "Cantidad")
    assert streak == ["Resolviste 4 ejercicios seguidos sin ayuda en Cantidad."]


def test_audit_log_records_teacher_access_to_student_data(w, db):
    ta, tb, room, (st,) = _published(w)
    w.c.get(f"/api/v1/students/{st['id']}", headers=ta)
    w.c.get(f"/api/v1/classrooms/{room}", headers=ta)
    w.c.get(f"/api/v1/support-flags?classroom_id={room}", headers=ta)
    w.c.get(f"/api/v1/analytics/classrooms/{room}/students/{st['id']}/progress", headers=ta)
    acts = {a.action for a in db.query(AuditLog)}
    assert {"students.read", "classrooms.read", "support_flags.list", "analytics.student_progress"} <= acts
    assert all(a.request_id for a in db.query(AuditLog))
    admin = w.login("admin@x.pe")
    assert len(w.c.get("/api/v1/audit-log", headers=admin).json()) >= 4
    assert w.c.get("/api/v1/audit-log", headers=ta).status_code == 403
    w.c.get(f"/api/v1/students/{uuid.uuid4()}", headers=tb)                              # acceso fallido: no se registra lectura
    assert db.query(AuditLog).filter(AuditLog.action == "students.read").count() == 1
