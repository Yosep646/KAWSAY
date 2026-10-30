"""Matrícula real sin duplicar estudiantes ni cruzar instituciones escolares."""
import uuid

from tests.test_student_courses import _login_student


def test_enroll_existing_student_in_new_academic_year_keeps_identity(w):
    school = w.school("Escuela rural")
    w.staff("TEACHER", "enroll-teacher@kawsay.com", school)
    teacher = w.login("enroll-teacher@kawsay.com")
    old_room = w.classroom(teacher, name="Cuarto 2026")
    student = w.student(teacher, old_room, 4, "Estudiante ya registrado")
    new_room = w.c.post("/api/v1/classrooms", headers=teacher,
                        json={"name": "Quinto 2027", "academic_year": 2027}).json()["id"]
    eligible = w.c.get(f"/api/v1/classrooms/{new_room}/eligible-students", headers=teacher)
    assert eligible.status_code == 200, eligible.text
    assert len(eligible.json()) == 1
    assert eligible.json()[0]["id"] == student["id"]
    assert eligible.json()[0]["previous_academic_year"] == 2026
    result = w.c.post(f"/api/v1/classrooms/{new_room}/enrollments", headers=teacher,
                      json={"student_id": student["id"]})
    assert result.status_code == 201, result.text
    assert result.json()["status"] == "ENROLLED"
    assert result.json()["grade_id"] == student["grade_id"]  # no promocionar a otro grado automáticamente
    classmates = w.c.get(f"/api/v1/classrooms/{new_room}", headers=teacher).json()["students"]
    assert [s["id"] for s in classmates] == [student["id"]]
    assert w.c.get(f"/api/v1/classrooms/{new_room}/eligible-students", headers=teacher).json() == []

    # Sin cuentas duplicadas, login anterior y curso anterior siguen intactos.
    assert w.c.get(f"/api/v1/classrooms/{old_room}", headers=teacher).json()["students"][0]["id"] == student["id"]
    assert _login_student(w, student)["Authorization"].startswith("Bearer ")
    assert w.c.post(f"/api/v1/classrooms/{new_room}/enrollments", headers=teacher,
                    json={"student_id": student["id"]}).status_code == 409


def test_enrollment_isolation_and_teacher_permissions(w):
    first = w.school("Escuela 1")
    other = w.school("Escuela 2")
    w.staff("TEACHER", "first-teacher@kawsay.com", first)
    w.staff("TEACHER", "other-teacher@kawsay.com", other)
    t1, t2 = w.login("first-teacher@kawsay.com"), w.login("other-teacher@kawsay.com")
    old_room = w.classroom(t1)
    student = w.student(t1, old_room, 3, "Ana de tercero")
    next_room = w.c.post("/api/v1/classrooms", headers=t1,
                         json={"name": "Nuevo 2027", "academic_year": 2027}).json()["id"]
    foreign_room = w.classroom(t2)
    for classroom_id, actor in ((next_room, t2), (foreign_room, t2)):
        denied = w.c.post(f"/api/v1/classrooms/{classroom_id}/enrollments", headers=actor,
                          json={"student_id": student["id"]})
        assert denied.status_code == 404
    assert w.c.get(f"/api/v1/classrooms/{next_room}/eligible-students", headers=t2).status_code == 404
    assert w.c.get(f"/api/v1/classrooms/{next_room}/eligible-students").status_code == 401

    # No se permite una segunda matrícula distinta del mismo año escolar.
    same_year_room = w.classroom(t1, name="Otra aula 2026")
    assert w.c.post(f"/api/v1/classrooms/{same_year_room}/enrollments", headers=t1,
                    json={"student_id": student["id"]}).status_code == 409
    assert w.c.post(f"/api/v1/classrooms/{next_room}/enrollments", headers=t1,
                    json={"student_id": str(uuid.uuid4())}).status_code == 404
