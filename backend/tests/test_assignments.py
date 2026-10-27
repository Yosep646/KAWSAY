import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.assignments.models import AssignmentVariant, StudentAssignment
from app.modules.assignments.service import create_ai_generated_variant_content
from tests.test_planning import FW

MC = {"type": "MULTIPLE_CHOICE", "prompt": "¿Cuál fracción es mayor?", "options": ["1/4", "3/4"],
      "correct_answer": {"index": 1}, "hints": ["Compara los numeradores"], "difficulty": 1}


def _env(w, grades=(1, 2, 3)):
    s1, s2 = w.school("E1"), w.school("E2")
    w.staff("ADMIN", "admin@x.pe")
    w.staff("TEACHER", "ta@x.pe", s1)
    w.staff("TEACHER", "tb@x.pe", s2)
    admin, ta, tb = w.login("admin@x.pe"), w.login("ta@x.pe"), w.login("tb@x.pe")
    fw_id = w.c.post("/api/v1/curriculum/frameworks", headers=admin, json=FW).json()["id"]
    tree = w.c.get(f"/api/v1/curriculum/frameworks/{fw_id}", headers=ta).json()
    math = next(s for s in tree["subjects"] if s["name"].startswith("Matem"))
    comp = math["competencies"][0]["id"]
    vid = w.c.post("/api/v1/planning/plans", headers=ta, json={"academic_year": 2026, "framework_id": fw_id,
                                                               "name": "Plan"}).json()["version"]["id"]
    period = w.c.post(f"/api/v1/planning/versions/{vid}/periods", headers=ta, json={"name": "I", "sequence": 1}).json()["id"]
    topics = {}
    for g in grades:
        u = w.c.post(f"/api/v1/planning/versions/{vid}/units", headers=ta, json={
            "period_id": period, "grade_id": w.grade_id(ta, g), "subject_id": math["id"], "title": f"Unidad {g}"}).json()["id"]
        topics[g] = w.c.post(f"/api/v1/planning/versions/{vid}/topics", headers=ta, json={
            "unit_id": u, "competency_id": comp, "title": f"Tema grado {g}",
            "learning_objective": f"Objetivo del grado {g}"}).json()["id"]
    for step, who in (("submit", ta), ("approve", admin), ("activate", admin)):
        assert w.c.post(f"/api/v1/planning/versions/{vid}/{step}", headers=who).status_code == 200
    room = w.classroom(ta)
    return admin, ta, tb, room, topics


def _create(w, ta, room, topics, grades=(1, 2, 3)):
    r = w.c.post("/api/v1/assignments", headers=ta, json={
        "classroom_id": room, "title": "Fracciones", "instructions": "Resuelve las preguntas",
        "grade_topics": [{"grade_id": w.grade_id(ta, g), "topic_id": topics[g]} for g in grades]})
    assert r.status_code == 201, r.text
    return r.json()


def _approve_all(w, ta, a):
    for v in a["variants"]:
        p = f"/api/v1/assignments/{a['id']}/variants/{v['id']}"
        w.c.patch(p, headers=ta, json={"title": f"Variante grado {v['grade_id']}"})
        assert w.c.put(p + "/questions", headers=ta, json={"questions": [MC]}).status_code == 200
        assert w.c.post(p + "/approve", headers=ta).status_code == 200


def test_requires_active_plan_and_respects_it(w):
    s = w.school()
    w.staff("TEACHER", "t@x.pe", s)
    t = w.login("t@x.pe")
    room = w.classroom(t)
    r = w.c.post("/api/v1/assignments", headers=t, json={
        "classroom_id": room, "title": "Sin plan", "instructions": "instrucciones",
        "grade_topics": [{"grade_id": 1, "topic_id": "00000000-0000-0000-0000-000000000000"}]})
    assert r.status_code == 409


def test_multigrade_creation_traceability_and_grade_topic_consistency(w):
    _, ta, tb, room, topics = _env(w)
    a = _create(w, ta, room, topics)
    assert [v["grade_id"] for v in a["variants"]] == sorted(v["grade_id"] for v in a["variants"])
    assert {v["learning_objective"] for v in a["variants"]} == {"Objetivo del grado 1", "Objetivo del grado 2", "Objetivo del grado 3"}
    assert all(v["status"] == "DRAFT" and v["source"] == "TEACHER" for v in a["variants"])
    # el tema del grado 3 NO sirve para el grado 1
    bad = w.c.post("/api/v1/assignments", headers=ta, json={
        "classroom_id": room, "title": "Mal", "instructions": "instrucciones",
        "grade_topics": [{"grade_id": w.grade_id(ta, 1), "topic_id": topics[3]}]})
    assert bad.status_code == 409
    assert w.c.post("/api/v1/assignments", headers=ta, json={  # grados repetidos
        "classroom_id": room, "title": "Rep", "instructions": "instrucciones",
        "grade_topics": [{"grade_id": 1, "topic_id": topics[1]}, {"grade_id": 1, "topic_id": topics[1]}]}).status_code == 422
    # otro docente no ve ni toca la tarea ni el aula
    assert w.c.get(f"/api/v1/assignments/{a['id']}", headers=tb).status_code == 404
    assert w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=tb).status_code == 404
    assert w.c.get("/api/v1/assignments", headers=tb).json() == []


def test_adaptive_pool_not_implemented_is_rejected(w):
    _, ta, _, room, topics = _env(w)
    r = w.c.post("/api/v1/assignments", headers=ta, json={
        "classroom_id": room, "title": "Pool", "instructions": "instrucciones", "mode": "ADAPTIVE_POOL",
        "grade_topics": [{"grade_id": w.grade_id(ta, 1), "topic_id": topics[1]}]})
    assert r.status_code == 422


def test_publish_requires_all_variants_approved_then_each_grade_gets_own_variant(w):
    _, ta, _, room, topics = _env(w, grades=(1, 2, 3, 4))
    kids = {g: w.student(ta, room, g, f"Alumno{g}") for g in (1, 2, 3)}
    kid4 = w.student(ta, room, 4, "Alumno4")           # grado 4: sin variante en esta tarea
    a = _create(w, ta, room, topics, grades=(1, 2, 3))
    assert w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=ta).status_code == 409   # nada aprobado
    # aprobar solo 2 de 3 => sigue bloqueado
    first, *rest = a["variants"]
    p = f"/api/v1/assignments/{a['id']}/variants/{first['id']}"
    w.c.put(p + "/questions", headers=ta, json={"questions": [MC]})
    w.c.post(p + "/approve", headers=ta)
    assert w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=ta).status_code == 409
    _approve_all(w, ta, {"id": a["id"], "variants": rest})
    pub = w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=ta)
    assert pub.status_code == 200, pub.text
    assert pub.json()["students_assigned"] == 3 and pub.json()["students_without_variant"] == [kid4["id"]]

    def tasks_for(kid):
        tok = w.c.post("/api/v1/auth/student-login", json={"login_code": kid["login_code"], "pin": kid["pin"],
                                                           "device_id": "44444444-4444-4444-4444-444444444444"}).json()
        return w.c.get("/api/v1/assignments/mine", headers={"Authorization": f"Bearer {tok['access_token']}"})

    for g, kid in kids.items():
        r = tasks_for(kid)
        body = r.json()
        assert len(body) == 1 and body[0]["learning_objective"] == f"Objetivo del grado {g}"   # variante correcta
        assert body[0]["grade_id"] == w.grade_id(ta, g)
        assert "correct_answer" not in r.text and "hints" not in r.text                         # sin respuestas
    assert tasks_for(kid4).json() == []                                                         # no recibe otra variante


def test_ai_generated_cannot_skip_teacher_review(w, db):
    _, ta, _, room, topics = _env(w)
    a = _create(w, ta, room, topics, grades=(1,))
    v = a["variants"][0]
    p = f"/api/v1/assignments/{a['id']}/variants/{v['id']}"
    w.c.put(p + "/questions", headers=ta, json={"questions": [MC]})
    row = db.get(AssignmentVariant, __import__("uuid").UUID(v["id"]))
    create_ai_generated_variant_content(db, row, "Título IA", "Instrucciones generadas por IA", "provider-x/model-y@prompt-1")
    assert w.c.post(p + "/approve", headers=ta).status_code == 409                       # no se aprueba directo
    assert w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=ta).status_code == 409
    assert w.c.post(p + "/review", headers=ta).status_code == 200                        # TEACHER_REVIEW
    assert w.c.post(p + "/approve", headers=ta).status_code == 200                       # aprobación humana
    detail = w.c.get(f"/api/v1/assignments/{a['id']}", headers=ta).json()["variants"][0]
    assert detail["source"] == "AI" and detail["approved_by"] and detail["generated_by"].startswith("provider-x")
    # editar tras aprobar: se anula la aprobación y vuelve a revisión
    w.c.patch(p, headers=ta, json={"instructions": "Instrucciones corregidas por la docente"})
    d2 = w.c.get(f"/api/v1/assignments/{a['id']}", headers=ta).json()["variants"][0]
    assert d2["status"] == "TEACHER_REVIEW" and d2["source"] == "AI_EDITED" and d2["approved_by"] is None


def test_db_blocks_approved_without_human_and_ai_without_provenance(w, db):
    _, ta, _, room, topics = _env(w)
    a = _create(w, ta, room, topics, grades=(1,))
    v = db.get(AssignmentVariant, __import__("uuid").UUID(a["variants"][0]["id"]))
    v.status = "APPROVED"          # sin approved_by
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    v = db.get(AssignmentVariant, __import__("uuid").UUID(a["variants"][0]["id"]))
    v.source = "AI"                # sin generated_by
    with pytest.raises(IntegrityError):
        db.commit()


def test_published_is_immutable(w):
    _, ta, _, room, topics = _env(w)
    a = _create(w, ta, room, topics, grades=(1,))
    _approve_all(w, ta, a)
    assert w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=ta).status_code == 200
    p = f"/api/v1/assignments/{a['id']}/variants/{a['variants'][0]['id']}"
    assert w.c.patch(p, headers=ta, json={"title": "Cambio tardío"}).status_code == 409
    assert w.c.put(p + "/questions", headers=ta, json={"questions": [MC]}).status_code == 409
    assert w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=ta).status_code == 409


def test_late_joiner_receives_published_assignment_of_own_grade(w, db):
    _, ta, _, room, topics = _env(w)
    a = _create(w, ta, room, topics)
    _approve_all(w, ta, a)
    w.c.post(f"/api/v1/assignments/{a['id']}/publish", headers=ta)
    new = w.student(ta, room, 2, "Tardio")
    sa = db.query(StudentAssignment).filter_by(student_user_id=__import__("uuid").UUID(new["id"])).one()
    v = db.get(AssignmentVariant, sa.variant_id)
    assert v.grade_id == w.grade_id(ta, 2)


@pytest.mark.parametrize("q", [
    {**MC, "correct_answer": {"index": 5}},                                              # índice fuera de rango
    {**MC, "options": ["solo una"]},                                                     # <2 opciones
    {"type": "NUMERIC", "prompt": "2+2", "correct_answer": {"value": "cuatro"}},         # no numérico
    {"type": "SHORT_TEXT", "prompt": "Capital", "correct_answer": {"accepted": []}},     # sin aceptadas
    {**MC, "unknown_field": 1},                                                          # mass assignment
])
def test_question_validation(w, q):
    _, ta, _, room, topics = _env(w)
    a = _create(w, ta, room, topics, grades=(1,))
    p = f"/api/v1/assignments/{a['id']}/variants/{a['variants'][0]['id']}/questions"
    assert w.c.put(p, headers=ta, json={"questions": [q]}).status_code == 422


def test_cannot_approve_variant_without_questions_and_student_blocked_from_teacher_api(w):
    _, ta, _, room, topics = _env(w)
    st = w.student(ta, room, 1)
    a = _create(w, ta, room, topics, grades=(1,))
    p = f"/api/v1/assignments/{a['id']}/variants/{a['variants'][0]['id']}"
    assert w.c.post(p + "/approve", headers=ta).status_code == 409
    tok = w.c.post("/api/v1/auth/student-login", json={"login_code": st["login_code"], "pin": st["pin"],
                                                       "device_id": "55555555-5555-5555-5555-555555555555"}).json()
    sh = {"Authorization": f"Bearer {tok['access_token']}"}
    assert w.c.get(f"/api/v1/assignments/{a['id']}", headers=sh).status_code == 403
    assert w.c.post(p + "/approve", headers=sh).status_code == 403
    assert w.c.get("/api/v1/assignments/mine", headers=ta).status_code == 403
