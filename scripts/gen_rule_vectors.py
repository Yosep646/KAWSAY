"""Genera shared/rules_vectors.json con la lógica de PRODUCCIÓN (backend/app/domain/adaptive.py).
Python y Dart (mobile/test/rules_test.dart) deben producir exactamente los mismos resultados."""
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.domain import adaptive as A  # noqa: E402

T0 = datetime(2026, 5, 4, 9, tzinfo=UTC)

EVAL = [
    ("MULTIPLE_CHOICE", {"index": 1}, {"index": 1}), ("MULTIPLE_CHOICE", {"index": 1}, {"index": 0}),
    ("MULTIPLE_CHOICE", {"index": 1}, {"index": "1"}), ("NUMERIC", {"value": 3.5, "tolerance": 0.1}, {"value": 3.45}),
    ("NUMERIC", {"value": 3.5, "tolerance": 0.1}, {"value": 3.7}), ("NUMERIC", {"value": 3}, {"value": "3"}),
    ("NUMERIC", {"value": 12}, {"value": 12}), ("SHORT_TEXT", {"accepted": ["Lima", "lima peru"]}, {"text": "  LIMA  "}),
    ("SHORT_TEXT", {"accepted": ["Lima"]}, {"text": "Cusco"}), ("SHORT_TEXT", {"accepted": ["a b"]}, {"text": "a    b"}),
    ("SHORT_TEXT", {"accepted": ["Lima"]}, {"text": 5}), ("DESCONOCIDO", {}, {}),
]
# cada escenario: lista de intentos (pregunta, n.º, correcto, pistas, minuto)
SCENARIOS = {
    "clean_streak": [(f"q{i}", 1, True, 0, i) for i in range(6)],
    "mixed_help": [("a", 1, True, 0, 0), ("b", 1, False, 1, 1), ("b", 2, True, 0, 2), ("c", 1, True, 2, 3), ("d", 1, False, 0, 4),
                   ("d", 2, False, 0, 5), ("d", 3, False, 0, 6), ("e", 1, True, 1, 7), ("f", 1, True, 0, 8)],
    "open_question_only": [("a", 1, False, 1, 0), ("a", 2, False, 0, 1)],
    "improving_12": [(f"q{i}", 1, False, 1, 2 * i) for i in range(6)] + [(f"q{i}", 2, True, 1, 2 * i + 1) for i in range(6)]
                    + [(f"r{i}", 1, True, 0, 100 + i) for i in range(6)],
    "few_results": [(f"q{i}", 1, True, 0, i) for i in range(4)],
}


def facts(rows):
    return [A.AttemptFact(f"{q}-{n}", q, n, ok, h, T0 + timedelta(minutes=m)) for q, n, ok, h, m in rows]


def main() -> dict:
    out = {"evaluate": [{"type": t, "correct": c, "answer": a, "expected": A.evaluate_answer(t, c, a)} for t, c, a in EVAL],
           "scenarios": []}
    for name, rows in SCENARIOS.items():
        res = A.question_results(facts(rows))
        score, count = A.compute_progress(res)
        msgs = A.motivation_messages(res, "Cantidad")
        out["scenarios"].append({
            "name": name, "attempts": [{"q": q, "n": n, "ok": ok, "hints": h, "minute": m} for q, n, ok, h, m in rows],
            "results": {r.question_id: {"score": r.score, "closed": r.closed, "hints": r.hints} for r in sorted(res, key=lambda r: r.question_id)},
            "progress": score, "evidence_count": count,
            "streak_message": next((m for m in msgs if m.startswith("Resolviste")), None),
            "improve_message": next((m for m in msgs if m.startswith("Tu precisión")), None)})
    return out


if __name__ == "__main__":
    path = ROOT / "shared" / "rules_vectors.json"
    path.write_text(json.dumps(main(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("escrito", path)
