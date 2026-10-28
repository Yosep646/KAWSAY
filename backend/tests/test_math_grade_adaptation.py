"""Acceptance tests for deterministic grade differentiation of teacher input.

No ML/LLM is involved; every generated question is reviewed and manually approved.
Synthetic students, real backend API, primary grades 1–6 and SQLite in CI.
"""
import pytest

from app.modules.assignments.math_grade_rules import generate_questions, parse_example
from tests.test_assignments import _env


@pytest.mark.parametrize(("raw", "expected"), [
    ("245 + 178 = ?", (245, 178, "+")),
    ("500 - 127", (500, 127, "-")),
    ("12 × 4", (12, 4, "×")),
    ("36 ÷ 6", (36, 6, "÷")),
])
def test_parse_teacher_math_example(raw, expected):
    ex = parse_example(raw)
    assert (ex.left, ex.right, ex.symbol) == expected


@pytest.mark.parametrize("raw", ["", "escribe un poema", "2+2; import os", "1 / 0",
                                       "7 - 12", "7 ÷ 3", "1**2", "9999999 + 1"])
def test_reject_unsafe_or_ambiguous_expressions(raw):
    with pytest.raises(ValueError):
        parse_example(raw)


@pytest.mark.parametrize("example", ["245 + 178", "500 - 127", "12 × 4", "36 ÷ 6"])
def test_rule_output_is_numeric_correct_without_ml(example):
    parsed = parse_example(example)
    for grade in range(1, 7):
        questions = generate_questions(parsed, grade, 4)
        assert len(questions) == 3
        assert all(q.difficulty in (1, 2, 3) and q.type == "NUMERIC" for q in questions)
        assert all(isinstance(q.correct_answer["value"], int) and q.correct_answer["value"] >= 0 for q in questions)
    fourth = generate_questions(parsed, 4, 4)
    assert parsed.original in fourth[0].prompt


def test_adapt_from_fourth_to_six_primary_grades_and_deliver_correct_students(w):
    _, teacher, other, room, topics = _env(w, grades=(1, 2, 3, 4, 5, 6))
    students = {n: w.student(teacher, room, n, f"Alumno número {n}") for n in range(1, 7)}
    a = w.c.post("/api/v1/assignments", headers=teacher, json={
        "classroom_id": room, "title": "Suma de números naturales",
        "instructions": "Resuelve el ejercicio base: 245 + 178 = ?",
        "mode": "MANUAL",
        "grade_topics": [{"grade_id": w.grade_id(teacher, n), "topic_id": topics[n]} for n in range(1, 7)],
    })
    assert a.status_code == 201, a.text
    assignment_id = a.json()["id"]
    url = f"/api/v1/assignments/{assignment_id}/adapt-math"
    request = {"source_grade_id": w.grade_id(teacher, 4), "example": "245 + 178 = ?"}
    assert w.c.post(url, json=request, headers=other).status_code == 404
    assert w.c.post(url, json=request).status_code == 401

    adapt = w.c.post(url, json=request, headers=teacher)
    assert adapt.status_code == 200, adapt.text
    payload = adapt.json()
    assert payload["engine"] == "RULES" and payload["status"] == "TEACHER_REVIEW"
    assert [v["grade_number"] for v in payload["variants"]] == list(range(1, 7))
    detail = w.c.get(f"/api/v1/assignments/{assignment_id}", headers=teacher).json()
    assert len(detail["variants"]) == 6

    first_prompts = []
    for number, variant in enumerate(detail["variants"], start=1):
        first = variant["questions"][0]
        first_prompts.append(first["prompt"])
        assert len(variant["questions"]) == 3
        assert variant["status"] == "TEACHER_REVIEW"
        assert variant["source"] == "TEACHER"
        assert variant["generated_by"].startswith("RULES/")
        assert variant["approved_by"] is None
        assert variant["validation_status"] == "NEEDS_REVIEW"
        assert first["correct_answer"]["value"] >= 0
        assert f"{number}.º" in variant["instructions"]
    assert len(set(first_prompts)) == 6
    assert "245 + 178" in first_prompts[3]
    assert detail["variants"][3]["questions"][0]["correct_answer"]["value"] == 423

    # Never publish without explicit human review, acknowledgment and approval.
    assert w.c.post(f"/api/v1/assignments/{assignment_id}/publish", headers=teacher).status_code == 409
    for variant in detail["variants"]:
        approval = f"/api/v1/assignments/{assignment_id}/variants/{variant['id']}/approve"
        assert w.c.post(approval, headers=teacher).status_code == 409
        assert w.c.post(approval + "?acknowledge_warnings=true", headers=teacher).status_code == 200
    published = w.c.post(f"/api/v1/assignments/{assignment_id}/publish", headers=teacher)
    assert published.status_code == 200, published.text
    assert published.json()["students_assigned"] == 6

    for number, kid in students.items():
        auth = w.c.post("/api/v1/auth/student-login", json={
            "login_code": kid["login_code"], "pin": kid["pin"],
            "device_id": "55555555-5555-5555-5555-555555555555",
        })
        assert auth.status_code == 200, auth.text
        token = {"Authorization": f"Bearer {auth.json()['access_token']}"}
        mine = w.c.get("/api/v1/assignments/mine", headers=token)
        assert mine.status_code == 200 and len(mine.json()) == 1
        task = mine.json()[0]
        assert task["grade_id"] == w.grade_id(teacher, number)
        assert len(task["questions"]) == 3
        assert f"{number}.º" in task["instructions"]
        assert "correct_answer" not in mine.text  # no answers in online student list
        assert "generated_by" not in mine.text

    assert w.c.post(url, json=request, headers=teacher).status_code == 409


def test_math_rule_refuses_missing_source_or_invalid_exercise_without_modifying_variants(w):
    _, teacher, _, room, topics = _env(w, grades=(2, 4))
    a = w.c.post("/api/v1/assignments", headers=teacher, json={
        "classroom_id": room, "title": "Sumas del aula", "instructions": "Resuelve 24 + 17",
        "mode": "MANUAL",
        "grade_topics": [{"grade_id": w.grade_id(teacher, n), "topic_id": topics[n]} for n in (2, 4)],
    }).json()
    endpoint = f"/api/v1/assignments/{a['id']}/adapt-math"
    assert w.c.post(endpoint, headers=teacher, json={
        "source_grade_id": w.grade_id(teacher, 1), "example": "24 + 17",
    }).status_code == 409
    assert w.c.post(endpoint, headers=teacher, json={
        "source_grade_id": w.grade_id(teacher, 4), "example": "24 + python",
    }).status_code == 422
    result = w.c.get(f"/api/v1/assignments/{a['id']}", headers=teacher).json()
    assert all(v["status"] == "DRAFT" and v["questions"] == [] for v in result["variants"])
