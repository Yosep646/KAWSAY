import pytest

from tests.conftest import PW  # noqa: F401


def _setup(w):
    school = w.school()
    w.staff("ADMIN", "admin@x.pe")
    w.staff("TEACHER", "ta@x.pe", school)
    w.staff("TEACHER", "tb@x.pe", school)
    return w.login("admin@x.pe"), w.login("ta@x.pe"), w.login("tb@x.pe")


def test_role_matrix(w):
    admin, ta, _ = _setup(w)
    st_room = w.classroom(ta)
    st = w.student(ta, st_room, 1)
    sh = {"Authorization": "Bearer " + w.c.post("/api/v1/auth/student-login", json={
        "login_code": st["login_code"], "pin": st["pin"],
        "device_id": "11111111-1111-1111-1111-111111111111"}).json()["access_token"]}
    # (método, ruta, headers, esperado)
    cases = [
        ("get", "/api/v1/users", ta, 403), ("get", "/api/v1/users", sh, 403), ("get", "/api/v1/users", admin, 200),
        ("get", "/api/v1/schools", ta, 403), ("get", "/api/v1/schools", sh, 403),
        ("get", "/api/v1/classrooms", sh, 403), ("get", "/api/v1/classrooms", admin, 403),
        ("get", f"/api/v1/students/{st['id']}", sh, 403), ("get", f"/api/v1/students/{st['id']}", ta, 200),
        ("get", "/api/v1/users", {}, 401), ("get", "/api/v1/classrooms", {}, 401),
        ("get", "/api/v1/curriculum/grades", sh, 200), ("get", "/api/v1/curriculum/grades", {}, 401),
    ]
    for method, path, headers, expected in cases:
        got = getattr(w.c, method)(path, headers=headers).status_code
        assert got == expected, (method, path, expected, got)


def test_teacher_cannot_access_other_teachers_data_idor(w):
    _, ta, tb = _setup(w)
    room_a, room_b = w.classroom(ta, "A"), w.classroom(tb, "B")
    st_a, st_b = w.student(ta, room_a, 2, "Ana"), w.student(tb, room_b, 2, "Beto")
    assert w.c.get(f"/api/v1/students/{st_a['id']}", headers=ta).status_code == 200      # A -> alumno A
    assert w.c.get(f"/api/v1/students/{st_b['id']}", headers=ta).status_code == 404      # A -> alumno B
    assert w.c.get(f"/api/v1/classrooms/{room_b}", headers=ta).status_code == 404
    assert w.c.post(f"/api/v1/students/{st_b['id']}/reset-pin", headers=ta).status_code == 404
    # tampoco puede crear alumnos en el aula ajena
    r = w.c.post("/api/v1/students", headers=ta, json={"display_name": "X", "grade_id": 1, "classroom_id": room_b})
    assert r.status_code == 404
    assert [c["id"] for c in w.c.get("/api/v1/classrooms", headers=ta).json()] == [room_a]


def test_student_cannot_see_other_student(w):
    _, ta, _ = _setup(w)
    room = w.classroom(ta)
    a, b = w.student(ta, room, 1, "A"), w.student(ta, room, 2, "B")
    tok = w.c.post("/api/v1/auth/student-login", json={"login_code": a["login_code"], "pin": a["pin"],
                                                       "device_id": "22222222-2222-2222-2222-222222222222"}).json()
    h = {"Authorization": f"Bearer {tok['access_token']}"}
    assert w.c.get(f"/api/v1/students/{b['id']}", headers=h).status_code == 403


def test_multigrade_classroom_keeps_individual_grade(w):
    _, ta, _ = _setup(w)
    room = w.classroom(ta)
    for grade, name in ((1, "Ana"), (2, "Luis"), (3, "Maria")):
        w.student(ta, room, grade, name)
    detail = w.c.get(f"/api/v1/classrooms/{room}", headers=ta).json()
    assert detail["grades_present"] == ["1.º PRIMARIA", "2.º PRIMARIA", "3.º PRIMARIA"]
    by_name = {s["display_name"]: s["grade_number"] for s in detail["students"]}
    assert by_name == {"Ana": 1, "Luis": 2, "Maria": 3}


def test_pin_returned_once_and_not_stored(w, db):
    _, ta, _ = _setup(w)
    st = w.student(ta, w.classroom(ta), 1)
    assert "pin" not in w.c.get(f"/api/v1/students/{st['id']}", headers=ta).text
    from app.modules.users.models import User
    assert st["pin"] not in db.get(User, __import__("uuid").UUID(st["id"])).password_hash


def test_reset_pin_revokes_sessions_and_old_pin(w):
    _, ta, _ = _setup(w)
    st = w.student(ta, w.classroom(ta), 1)
    dev = "33333333-3333-3333-3333-333333333333"
    tok = w.c.post("/api/v1/auth/student-login", json={"login_code": st["login_code"], "pin": st["pin"],
                                                       "device_id": dev}).json()
    new_pin = w.c.post(f"/api/v1/students/{st['id']}/reset-pin", headers=ta).json()["pin"]
    assert w.c.post("/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]}).status_code == 401
    assert w.c.post("/api/v1/auth/student-login", json={"login_code": st["login_code"], "pin": st["pin"],
                                                        "device_id": dev}).status_code == 401
    assert w.c.post("/api/v1/auth/student-login", json={"login_code": st["login_code"], "pin": new_pin,
                                                        "device_id": dev}).status_code == 200


def test_teacher_creation_requires_school_and_unique_email(w):
    admin, _, _ = _setup(w)
    base = {"role": "TEACHER", "email": "n@x.pe", "password": PW, "display_name": "N"}
    assert w.c.post("/api/v1/users", headers=admin, json=base).status_code == 422
    sid = w.c.get("/api/v1/schools", headers=admin).json()[0]["id"]
    assert w.c.post("/api/v1/users", headers=admin, json={**base, "school_id": sid}).status_code == 201
    assert w.c.post("/api/v1/users", headers=admin, json={**base, "school_id": sid}).status_code == 409
    weak = w.c.post("/api/v1/users", headers=admin, json={**base, "email": "m@x.pe", "password": "corta",
                                                          "school_id": sid})
    assert weak.status_code == 422


def test_invalid_grade_and_duplicate_classroom(w):
    _, ta, _ = _setup(w)
    room = w.classroom(ta)
    r = w.c.post("/api/v1/students", headers=ta, json={"display_name": "X", "grade_id": 9999, "classroom_id": room})
    assert r.status_code == 404
    dup = w.c.post("/api/v1/classrooms", headers=ta, json={"name": "Aula Multigrado", "academic_year": 2026})
    assert dup.status_code == 409


@pytest.mark.parametrize("path", ["/api/v1/students/not-a-uuid", "/api/v1/classrooms/123"])
def test_malformed_ids_rejected(w, path):
    _, ta, _ = _setup(w)
    assert w.c.get(path, headers=ta).status_code == 422
