"""Pruebas de aceptación de entrada/salida: docente -> tareas -> estudiante.

Datos y credenciales sintéticos. El fixture w usa SQLite temporal y aislada;
ninguna llamada apunta al despliegue de Render.
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.modules.assignments.models import Assignment
from app.modules.learning.models import LearningAttempt
from tests.test_assignments import _create, _env
from tests.test_sync_reto10 import _login, _pull, _push


def _question(kind: str, grade: int) -> dict:
    if kind == "MULTIPLE_CHOICE":
        return {
            "type": kind, "prompt": f"Grado {grade}: ¿Cuánto es 2 + 3?",
            "options": ["4", "5", "6"], "correct_answer": {"index": 1},
            "hints": ["Cuenta con los dedos"], "explanation": "Dos más tres son cinco", "difficulty": 1,
        }
    if kind == "NUMERIC":
        return {
            "type": kind, "prompt": f"Grado {grade}: ¿Cuánto es 14 + 8?",
            "options": None, "correct_answer": {"value": 22, "tolerance": 0},
            "hints": [], "explanation": "Catorce más ocho son veintidós", "difficulty": 2,
        }
    return {
        "type": "SHORT_TEXT", "prompt": f"Grado {grade}: escribe el resultado de 100 + 20",
        "options": None, "correct_answer": {"accepted": ["120"]},
        "hints": [], "explanation": "Cien más veinte son ciento veinte", "difficulty": 3,
    }


def _event(student_assignment_id: str, question_id: str, answer: dict) -> dict:
    return {
        "event_id": str(uuid.uuid4()), "type": "attempt.created",
        "payload": {
            "student_assignment_id": student_assignment_id, "question_id": question_id,
            "attempt_number": 1, "answer": answer, "hints_used": 0,
            "response_time_ms": 3000,
            "client_created_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        },
    }


def test_teacher_inputs_become_visible_to_correct_grades_and_answers_return_to_server(w, db):
    """Entradas válidas + salidas reales del API, con tres tipos de pregunta."""
    _, teacher, other_teacher, room, topics = _env(w, grades=(1, 2, 3))
    students = {g: w.student(teacher, room, g, f"Estudiante prueba {g}") for g in (1, 2, 3)}
    assignment = _create(w, teacher, room, topics, grades=(1, 2, 3))
    assignment_id = assignment["id"]
    responses = {
        1: {"index": 1},
        2: {"value": 22},
        3: {"text": "120"},
    }
    content_types = {1: "MULTIPLE_CHOICE", 2: "NUMERIC", 3: "SHORT_TEXT"}

    # Entrada del docente: instrucciones y pregunta particular de cada grado.
    for grade, variant in zip((1, 2, 3), assignment["variants"], strict=True):
        url = f"/api/v1/assignments/{assignment_id}/variants/{variant['id']}"
        instructions = f"Indicaciones visibles para {grade}.º grado: resuelve la suma."
        saved = w.c.patch(url, headers=teacher, json={"instructions": instructions})
        assert saved.status_code == 200, saved.text
        question = _question(content_types[grade], grade)
        submitted = w.c.put(url + "/questions", headers=teacher, json={"questions": [question]})
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["count"] == 1

    # Salida al docente: lo que guardó vuelve a la vista de revisión.
    detail = w.c.get(f"/api/v1/assignments/{assignment_id}", headers=teacher)
    assert detail.status_code == 200, detail.text
    for grade, variant in zip((1, 2, 3), detail.json()["variants"], strict=True):
        assert variant["instructions"] == f"Indicaciones visibles para {grade}.º grado: resuelve la suma."
        assert len(variant["questions"]) == 1
        assert variant["questions"][0]["type"] == content_types[grade]
        assert "correct_answer" in variant["questions"][0]
        assert variant["status"] == "DRAFT"

    # No debe estar disponible al alumno antes de publicación y aprobación.
    student_tokens = {grade: _login(w, student) for grade, student in students.items()}
    assert all(not _pull(w, token)["tasks"] for token in student_tokens.values())
    assert w.c.post(f"/api/v1/assignments/{assignment_id}/publish", headers=teacher).status_code == 409

    # La revisión humana es obligatoria, no automática.
    for variant in detail.json()["variants"]:
        approve = w.c.post(f"/api/v1/assignments/{assignment_id}/variants/{variant['id']}/approve", headers=teacher)
        assert approve.status_code == 200, approve.text
    published = w.c.post(f"/api/v1/assignments/{assignment_id}/publish", headers=teacher)
    assert published.status_code == 200, published.text
    assert published.json()["students_assigned"] == 3

    # Salida del estudiante: solo la variante y las instrucciones de SU grado.
    for grade, token in student_tokens.items():
        tasks = _pull(w, token)["tasks"]
        assert len(tasks) == 1
        task = tasks[0]
        assert task["grade_id"] == w.grade_id(teacher, grade)
        assert task["instructions"] == f"Indicaciones visibles para {grade}.º grado: resuelve la suma."
        assert task["questions"][0]["type"] == content_types[grade]
        assert task["questions"][0]["prompt"].startswith(f"Grado {grade}:")
        # El endpoint resumido no debe filtrar la clave de respuestas.
        student_summary = w.c.get("/api/v1/assignments/mine", headers=token)
        assert student_summary.status_code == 200
        assert "correct_answer" not in student_summary.text
        # Offline: se entrega lo necesario al dispositivo autenticado.
        assert task["questions"][0]["correct_answer"] == _question(content_types[grade], grade)["correct_answer"]
        response = _push(w, token, [_event(task["student_assignment_id"], task["questions"][0]["id"], responses[grade])])
        assert response[0]["status"] == "ACKED"
        progress = w.c.get(
            f"/api/v1/sync/tasks/{task['student_assignment_id']}/attempts"
            "?device_id=66666666-6666-6666-6666-666666666666",
            headers=token,
        )
        assert progress.status_code == 200
        assert progress.json()["questions"][0]["closed"] is True

    assert db.query(LearningAttempt).count() == 3
    assert all(row.is_correct for row in db.query(LearningAttempt).all())
    # No permitir listar/revisar actividades pertenecientes a otra institución.
    assert w.c.get(f"/api/v1/assignments/{assignment_id}", headers=other_teacher).status_code == 404


def test_invalid_question_inputs_never_overwrite_previous_published_intent(w):
    """Pedir datos incorrectos devuelve 422 y no deja ejercicios inválidos."""
    _, teacher, _, room, topics = _env(w, grades=(1,))
    a = _create(w, teacher, room, topics, grades=(1,))
    url = f"/api/v1/assignments/{a['id']}/variants/{a['variants'][0]['id']}/questions"
    valid = _question("MULTIPLE_CHOICE", 1)
    assert w.c.put(url, headers=teacher, json={"questions": [valid]}).status_code == 200
    invalid = (
        [],  # al menos una pregunta
        [{**valid, "prompt": "a"}],  # enunciado demasiado corto
        [{**valid, "difficulty": 0}],  # fuera del rango 1–3
        [{**valid, "correct_answer": {"index": 99}}],  # fuera de opciones
        [{**valid, "options": ["una"]}],  # selección múltiple incompleta
        [{**valid, "hints": ["x"] * 6}],  # demasiadas pistas
        [valid] * 31,  # máximo 30 preguntas
        [{**valid, "admin": True}],  # campo extra no autorizado
    )
    for questions in invalid:
        rejected = w.c.put(url, headers=teacher, json={"questions": questions})
        assert rejected.status_code == 422, (questions, rejected.text)
        review = w.c.get(f"/api/v1/assignments/{a['id']}", headers=teacher).json()
        assert [q["prompt"] for q in review["variants"][0]["questions"]] == [valid["prompt"]]

    # Un alumno no puede editar ni aprobar preguntas.
    student = w.student(teacher, room, 1, "Alumno sintético")
    token = _login(w, student)
    assert w.c.put(url, headers=token, json={"questions": [valid]}).status_code == 403
    assert w.c.post(url.removesuffix("/questions") + "/approve", headers=token).status_code == 403


def test_invalid_assignment_inputs_and_no_access_do_not_create_records(w, db):
    _, teacher, other_teacher, room, topics = _env(w, grades=(1,))
    valid = {
        "classroom_id": room, "title": "Sumas naturales",
        "instructions": "Practica las sumas con cantidades de la comunidad.",
        "grade_topics": [{"grade_id": w.grade_id(teacher, 1), "topic_id": topics[1]}],
    }
    for change in (
        {"title": ""},
        {"title": "x" * 301},
        {"instructions": "no"},
        {"mode": "ADAPTIVE_POOL"},
        {"mode": "desconocido"},
        {"grade_topics": []},
        {"grade_topics": valid["grade_topics"] * 2},
        {"admin_override": True},
    ):
        res = w.c.post("/api/v1/assignments", headers=teacher, json=valid | change)
        assert res.status_code == 422, (change, res.text)
    assert w.c.post("/api/v1/assignments", json=valid).status_code == 401
    assert w.c.post("/api/v1/assignments", headers=other_teacher, json=valid).status_code == 404
    assert db.query(Assignment).count() == 0
