"""Pruebas de extremo a extremo: docente crea estudiante con correo y contraseña.

Se conserva el acceso heredado con código/PIN para estudiantes sin correo.
La clave nunca se devuelve en la API, en logs ni en el modelo de base de datos.
"""
import uuid

from app.modules.students.email_models import StudentEmailLogin
from app.modules.users.models import User
from tests.conftest import new_device

STUDENT_EMAIL = "estudiante@escuela.pe"
STUDENT_PASSWORD = "UnAccesoSeguro#2026"
RESET_PASSWORD = "OtroAccesoSeguro#2026"


def setup_classroom(w):
    school = w.school()
    w.staff("TEACHER", "tutora@escuela.pe", school)
    teacher = w.login("tutora@escuela.pe")
    classroom = w.classroom(teacher)
    grade = w.grade_id(teacher, 3)
    return teacher, classroom, grade


def test_teacher_creates_student_email_password_and_student_can_login(w, db):
    teacher, room, grade = setup_classroom(w)
    resp = w.c.post("/api/v1/students", headers=teacher, json={
        "display_name": "María Huamán", "grade_id": grade, "classroom_id": room,
        "email": STUDENT_EMAIL.upper(), "password": STUDENT_PASSWORD,
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == STUDENT_EMAIL
    assert data["pin"] is None and data["login_code"] is None
    assert "password" not in data
    saved = db.get(User, uuid.UUID(data["id"]))
    assert saved.role == "STUDENT"
    assert saved.password_hash.startswith("$argon2")
    assert STUDENT_PASSWORD not in saved.password_hash
    email = db.get(StudentEmailLogin, saved.id)
    assert email is not None and email.email == STUDENT_EMAIL

    bad = w.c.post("/api/v1/auth/student-email-login", json={
        "email": STUDENT_EMAIL, "password": "Contraseña incorrecta", "device_id": new_device(),
    })
    assert bad.status_code == 401
    token = w.c.post("/api/v1/auth/student-email-login", json={
        "email": STUDENT_EMAIL, "password": STUDENT_PASSWORD, "device_id": new_device(),
    })
    assert token.status_code == 200, token.text
    assert token.json()["user"]["role"] == "STUDENT"
    assert w.c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token.json()['access_token']}"}).status_code == 200
    assert w.c.post("/api/v1/auth/login", json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}).status_code == 401
    detail = w.c.get(f"/api/v1/students/{data['id']}", headers=teacher)
    assert detail.status_code == 200 and detail.json()["email"] == STUDENT_EMAIL
    assert detail.json()["login_code"] is None


def test_email_password_requires_both_valid_and_unique(w):
    teacher, room, grade = setup_classroom(w)
    base = {"display_name": "Carla", "grade_id": grade, "classroom_id": room}
    for patch in (
        {"email": STUDENT_EMAIL},
        {"password": STUDENT_PASSWORD},
        {"email": "invalido", "password": STUDENT_PASSWORD},
        {"email": STUDENT_EMAIL, "password": "corta"},
    ):
        r = w.c.post("/api/v1/students", headers=teacher, json=base | patch)
        assert r.status_code == 422, r.text
    good = w.c.post("/api/v1/students", headers=teacher, json=base | {
        "email": STUDENT_EMAIL, "password": STUDENT_PASSWORD})
    assert good.status_code == 201, good.text
    dup = w.c.post("/api/v1/students", headers=teacher, json=base | {
        "email": STUDENT_EMAIL.upper(), "password": RESET_PASSWORD})
    assert dup.status_code == 409
    assert "password" not in good.text


def test_only_classroom_teacher_can_reset_student_password_and_sessions_revoked(w):
    teacher, room, grade = setup_classroom(w)
    school = w.school("Otra institución")
    w.staff("TEACHER", "intruso@escuela.pe", school)
    other = w.login("intruso@escuela.pe")
    data = w.c.post("/api/v1/students", headers=teacher, json={
        "display_name": "Estudiante", "grade_id": grade, "classroom_id": room,
        "email": STUDENT_EMAIL, "password": STUDENT_PASSWORD,
    }).json()
    student_id = data["id"]
    assert w.c.post(f"/api/v1/students/{student_id}/reset-password",
                    headers=other, json={"password": RESET_PASSWORD}).status_code == 404
    assert w.c.post(f"/api/v1/students/{student_id}/reset-pin", headers=teacher).status_code == 409
    old = w.c.post("/api/v1/auth/student-email-login", json={
        "email": STUDENT_EMAIL, "password": STUDENT_PASSWORD, "device_id": new_device()}).json()
    update = w.c.post(f"/api/v1/students/{student_id}/reset-password",
                      headers=teacher, json={"password": RESET_PASSWORD})
    assert update.status_code == 204, update.text
    assert w.c.post("/api/v1/auth/refresh", json={"refresh_token": old["refresh_token"]}).status_code == 401
    assert w.c.post("/api/v1/auth/student-email-login", json={
        "email": STUDENT_EMAIL, "password": STUDENT_PASSWORD, "device_id": new_device()}).status_code == 401
    assert w.c.post("/api/v1/auth/student-email-login", json={
        "email": STUDENT_EMAIL, "password": RESET_PASSWORD, "device_id": new_device()}).status_code == 200


def test_legacy_code_pin_still_works(w):
    teacher, room, grade = setup_classroom(w)
    r = w.c.post("/api/v1/students", headers=teacher, json={
        "display_name": "Acceso antiguo", "grade_id": grade, "classroom_id": room})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["pin"] and data["login_code"] and data["email"] is None
    login = w.c.post("/api/v1/auth/student-login", json={
        "login_code": data["login_code"], "pin": data["pin"], "device_id": new_device()})
    assert login.status_code == 200
