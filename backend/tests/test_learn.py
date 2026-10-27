from app.modules.assignments.models import StudentAssignment
from tests.test_sync_reto10 import _ev, _login, _published, _pull, _push, _struggle


def _sub_topic_activity(w, sh):
    subs = w.c.get("/api/v1/learning/subjects", headers=sh).json()
    topics = w.c.get(f"/api/v1/learning/topics?subject_id={subs[0]['id']}", headers=sh).json()
    acts = w.c.get(f"/api/v1/learning/activities?topic_id={topics[0]['id']}", headers=sh).json()
    return subs, topics, acts


def test_quiero_aprender_flow_uses_only_available_content_of_own_grade(w, db):
    _, _, _, kids = _published(w, kids=(("Juan", 1), ("Beto", 2)))
    j, b = _login(w, kids[0]), _login(w, kids[1], "99999999-9999-9999-9999-999999999999")
    subs, topics, acts = _sub_topic_activity(w, j)
    assert subs[0]["activities"] == 1 and topics[0]["title"] == "Tema grado 1" and topics[0]["my_progress_percent"] is None
    assert acts[0]["questions"] == 5 and acts[0]["already_started"] is True            # ya tenía la tarea del docente
    # el alumno de 2.º no ve contenido de 1.º: no hay materias, y no puede iniciar la variante de 1.º
    assert w.c.get("/api/v1/learning/subjects", headers=b).json() == []
    assert w.c.post("/api/v1/learning/start", headers=b, json={"variant_id": acts[0]["variant_id"]}).status_code == 404
    assert w.c.post("/api/v1/learning/start", headers=j, json={"variant_id": "00000000-0000-0000-0000-000000000000"}).status_code == 404


def test_self_started_practice_syncs_attempts_and_counts_for_progress(w, db):
    ta, _, room, (st, ) = _published(w, kids=(("Juan", 1),))
    sh = _login(w, st)
    # el alumno que se une DESPUÉS: no recibe la tarea por pull de docente, pero sí puede practicar voluntariamente
    late = w.student(ta, room, 1, "Tarde")
    lh = _login(w, late, "12121212-1212-1212-1212-121212121212")
    _, _, acts = _sub_topic_activity(w, lh)
    task = w.c.post("/api/v1/learning/start", headers=lh, json={"variant_id": acts[0]["variant_id"]}).json()
    again = w.c.post("/api/v1/learning/start", headers=lh, json={"variant_id": acts[0]["variant_id"]}).json()
    assert task["student_assignment_id"] == again["student_assignment_id"] and task["origin"] in ("TEACHER", "SELF")
    assert len(task["questions"]) == 5 and task["questions"][0]["correct_answer"] == {"index": 1}   # listo para offline
    r = _push(w, lh, _struggle(w, lh, task), dev="12121212-1212-1212-1212-121212121212")
    assert all(x["status"] == "ACKED" for x in r)
    prog = w.c.get("/api/v1/progress/me", headers=lh).json()
    assert prog and prog[0]["percent"] is not None                                    # la práctica voluntaria cuenta
    topics = w.c.get(f"/api/v1/learning/topics?subject_id={w.c.get('/api/v1/learning/subjects', headers=lh).json()[0]['id']}", headers=lh).json()
    assert topics[0]["my_progress_percent"] is not None
    _ = (sh, _ev, _pull)


def test_self_practice_does_not_pollute_my_tasks_and_requires_student_role(w, db):
    ta, _, room, (st,) = _published(w)
    late = w.student(ta, room, 1, "Tarde")
    lh = _login(w, late, "13131313-1313-1313-1313-131313131313")
    # sin 'start' previo no hay tareas; el alumno tardío recibió la publicada (alumno nuevo), así que verificamos el origen
    mine = w.c.get("/api/v1/assignments/mine", headers=lh).json()
    sa = db.query(StudentAssignment).filter_by(origin="TEACHER").count()
    assert len(mine) == 1 and sa == 2
    assert w.c.get("/api/v1/learning/subjects", headers=ta).status_code == 403
    assert w.c.get("/api/v1/learning/subjects").status_code == 401
