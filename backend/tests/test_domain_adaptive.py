from datetime import UTC, datetime, timedelta

from app.domain import adaptive as A

T0 = datetime(2026, 5, 4, 10, tzinfo=UTC)


def f(q, n, ok, hints=0, minutes=0, day=0):
    return A.AttemptFact(f"{q}-{n}", q, n, ok, hints, T0 + timedelta(days=day, minutes=minutes))


def test_scoring_levels_of_help():
    r = {x.question_id: x for x in A.question_results([
        f("clean", 1, True), f("h1", 1, True, 1), f("w1", 1, False), f("w1", 2, True),
        f("h2", 1, True, 2), f("w2", 1, False), f("w2", 2, False), f("w2", 3, True),
        f("fail", 1, False), f("fail", 2, False), f("fail", 3, False)])}
    assert (r["clean"].score, r["h1"].score, r["w1"].score, r["h2"].score, r["w2"].score, r["fail"].score) == \
           (1.0, 0.7, 0.7, 0.4, 0.4, 0.0)


def test_open_question_is_not_evidence_yet():
    r = A.question_results([f("q", 1, False)])          # 1 error, aún puede reintentar
    assert not r[0].closed
    assert A.compute_progress(r) == (None, 0) and A.detect_difficulty(r) is None


def test_progress_requires_min_evidence_and_never_invents_percentage():
    few = A.question_results([f(f"q{i}", 1, True) for i in range(4)])
    assert A.compute_progress(few) == (None, 4)
    enough = A.question_results([f(f"q{i}", 1, True, minutes=i) for i in range(5)])
    assert A.compute_progress(enough) == (1.0, 5)
    assert A.level_for(None) is None and A.level_for(0.3) == "REFUERZO" and A.level_for(0.7) == "ESPERADO" \
        and A.level_for(0.9) == "DESAFIO"


def test_difficulty_recommendation_requires_evidence_and_uses_bounded_levels():
    assert A.difficulty_recommendation(None, 0)["action"] == "INSUFFICIENT_EVIDENCE"
    assert A.difficulty_recommendation(1.0, 4)["suggested_difficulty"] is None
    assert A.difficulty_recommendation(0.3, 5)["action"] == "LOWER"
    assert A.difficulty_recommendation(0.5, 5)["suggested_difficulty"] == 2
    assert A.difficulty_recommendation(0.85, 5)["action"] == "MAINTAIN"
    assert A.difficulty_recommendation(0.9, 5)["action"] == "RAISE"


def test_progress_weights_recent_more():
    old_bad = [f(f"q{i}", n, False, minutes=i) for i in range(3) for n in (1, 2, 3)]            # 3 fallos antiguos
    recent_good = [f(f"g{i}", 1, True, minutes=100 + i) for i in range(5)]
    score, _ = A.compute_progress(A.question_results(old_bad + recent_good))
    assert score is not None and score > 0.7


def test_detector_4_of_5_with_evidence():
    facts = []
    for i in range(4):  # 4 ejercicios con dificultad (3 fallos y pistas)
        facts += [f(f"d{i}", 1, False, 1, minutes=i), f(f"d{i}", 2, False, 1, minutes=i + 1), f(f"d{i}", 3, False, 0, minutes=i + 2)]
    facts.append(f("ok", 1, True, minutes=50))
    finding = A.detect_difficulty(A.question_results(facts))
    assert finding and finding.difficult == 4 and finding.window == 5 and finding.hints_total == 8
    assert finding.wrong_attempts_total == 12 and len(finding.results) == 5


def test_detector_not_triggered_3_of_5_or_insufficient_window():
    facts = []
    for i in range(3):
        facts += [f(f"d{i}", n, False, minutes=i * 5 + n) for n in (1, 2, 3)]
    facts += [f("a", 1, True, minutes=60), f("b", 1, True, minutes=61)]
    assert A.detect_difficulty(A.question_results(facts)) is None
    assert A.detect_difficulty(A.question_results(facts[:6])) is None   # solo 2 cerrados


def test_evaluate_answer_server_side():
    assert A.evaluate_answer("MULTIPLE_CHOICE", {"index": 1}, {"index": 1}) is True
    assert A.evaluate_answer("MULTIPLE_CHOICE", {"index": 1}, {"index": True}) is None
    assert A.evaluate_answer("NUMERIC", {"value": 3.5, "tolerance": 0.1}, {"value": 3.45}) is True
    assert A.evaluate_answer("NUMERIC", {"value": 3}, {"value": "3"}) is None
    assert A.evaluate_answer("SHORT_TEXT", {"accepted": ["Lima"]}, {"text": "  lima "}) is True
    assert A.evaluate_answer("SHORT_TEXT", {"accepted": ["Lima"]}, {"text": "Cusco"}) is False
    assert A.evaluate_answer("DESCONOCIDO", {}, {}) is None
