"""Contrato del catálogo curricular: plan activo -> curso visible -> tarea -> sync."""
from tests.test_planning import _env


def _login_student(w, student):
    response = w.c.post("/api/v1/auth/student-login", json={
        "login_code": student["login_code"], "pin": student["pin"],
        "device_id": "66666666-6666-6666-6666-666666666666",
    })
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _catalog_env(w):
    admin, teacher, other_teacher, fw_id, tree = _env(w)
    classroom = w.classroom(teacher)
    primary = w.student(teacher, classroom, 4, "Estudiante de 4")
    fifth = w.student(teacher, classroom, 5, "Estudiante de 5")
    room_other = w.classroom(other_teacher, name="Aula otra escuela")
    other = w.student(other_teacher, room_other, 4, "Otra institución")

    version = w.c.post("/api/v1/planning/plans", headers=teacher, json={
        "academic_year": 2026, "framework_id": fw_id, "name": "Plan cursos",
    }).json()["version"]["id"]
    period = w.c.post(f"/api/v1/planning/versions/{version}/periods", headers=teacher, json={
        "name": "Primer periodo", "sequence": 1,
    }).json()["id"]
    topics = {}
    for subject in tree["subjects"]:
        unit_response = w.c.post(f"/api/v1/planning/versions/{version}/units", headers=teacher, json={
            "period_id": period, "grade_id": w.grade_id(teacher, 4),
            "subject_id": subject["id"], "title": f"Unidad {subject['name']}",
        })
        assert unit_response.status_code == 201, unit_response.text
        topic_response = w.c.post(f"/api/v1/planning/versions/{version}/topics", headers=teacher, json={
            "unit_id": unit_response.json()["id"], "competency_id": subject["competencies"][0]["id"],
            "title": f"Tema {subject['name']}", "learning_objective": "Aprendizaje del cuarto grado",
        })
        assert topic_response.status_code == 201, topic_response.text
        topics[subject["name"]] = topic_response.json()["id"]

    return admin, teacher, other_teacher, classroom, primary, fifth, other, version, topics


def _activate(w, admin, teacher, version):
    for action, who in (("submit", teacher), ("approve", admin), ("activate", admin)):
        result = w.c.post(f"/api/v1/planning/versions/{version}/{action}", headers=who)
        assert result.status_code == 200, result.text


def test_courses_exist_without_published_tasks_only_with_active_plan(w):
    admin, teacher, _, _, primary, fifth, other, version, _ = _catalog_env(w)
    student_auth = _login_student(w, primary)
    fifth_auth = _login_student(w, fifth)
    other_auth = _login_student(w, other)

    # Nunca mostrar un plan en borrador como si fuera el curso oficial.
    assert w.c.get("/api/v1/sync/courses", headers=student_auth).json() == []
    _activate(w, admin, teacher, version)

    response = w.c.get("/api/v1/sync/courses", headers=student_auth)
    assert response.status_code == 200, response.text
    courses = response.json()
    assert len(courses) == 2
    assert {c["name"] for c in courses} == {"Matemática (DEMO)", "Comunicación (DEMO)"}
    assert all(c["is_demo"] is True for c in courses)
    assert all(c["academic_year"] == 2026 for c in courses)
    assert all(c["classroom_name"] == "Aula Multigrado" for c in courses)
    assert len({c["id"] for c in courses}) == 2
    assert w.c.get("/api/v1/sync/courses", headers=fifth_auth).json() == []
    assert w.c.get("/api/v1/sync/courses", headers=other_auth).json() == []

    pulled = w.c.get("/api/v1/sync/pull?cursor=0", headers=student_auth)
    assert pulled.status_code == 200, pulled.text
    assert len(pulled.json()["courses"]) == 2
    assert pulled.json()["tasks"] == []

    assert w.c.get("/api/v1/sync/courses", headers=teacher).status_code == 403
    assert w.c.get("/api/v1/sync/courses").status_code == 401


def test_teacher_publication_links_to_student_course_and_keeps_grade(w):
    admin, teacher, _, classroom, primary, fifth, _, version, topics = _catalog_env(w)
    _activate(w, admin, teacher, version)
    grade = w.grade_id(teacher, 4)
    created = w.c.post("/api/v1/assignments", headers=teacher, json={
        "classroom_id": classroom, "title": "Sumas del cuarto grado",
        "instructions": "Resuelve y explica tu procedimiento",
        "grade_topics": [{"grade_id": grade, "topic_id": topics["Matemática (DEMO)"]}],
    })
    assert created.status_code == 201, created.text
    assignment = created.json()
    variant = assignment["variants"][0]["id"]
    base = f"/api/v1/assignments/{assignment['id']}/variants/{variant}"
    assert w.c.put(base + "/questions", headers=teacher, json={"questions": [{
        "type": "MULTIPLE_CHOICE", "prompt": "¿Cuánto es dos más tres?",
        "options": ["4", "5"], "correct_answer": {"index": 1}, "hints": ["Cuenta"],
    }]}).status_code == 200
    assert w.c.post(base + "/approve", headers=teacher).status_code == 200
    published = w.c.post(f"/api/v1/assignments/{assignment['id']}/publish", headers=teacher)
    assert published.status_code == 200, published.text

    fourth_auth, fifth_auth = _login_student(w, primary), _login_student(w, fifth)
    fourth_data = w.c.get("/api/v1/sync/pull", headers=fourth_auth).json()
    fifth_data = w.c.get("/api/v1/sync/pull", headers=fifth_auth).json()

    assert {c["name"] for c in fourth_data["courses"]} == {"Matemática (DEMO)", "Comunicación (DEMO)"}
    assert len(fourth_data["tasks"]) == 1
    task = fourth_data["tasks"][0]
    assert task["subject"] == "Matemática (DEMO)"
    assert task["grade_id"] == grade
    assert task["questions"][0]["correct_answer"] == {"index": 1}
    assert fifth_data["tasks"] == []
    # Los cursos pueden seguir apareciendo sin actividades cuando el docente no publica.
    assert {c["name"] for c in fourth_data["courses"]} - {task["subject"]} == {"Comunicación (DEMO)"}
