"""Los vectores compartidos (shared/rules_vectors.json) deben coincidir con la lógica de producción.
Dart (mobile/test/rules_test.dart) los consume: así servidor y app móvil no se desincronizan."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_vectors_file_is_up_to_date_with_production_rules():
    sys.path.insert(0, str(ROOT / "scripts"))
    import gen_rule_vectors
    fresh = json.loads(json.dumps(gen_rule_vectors.main(), ensure_ascii=False))
    assert json.loads((ROOT / "shared" / "rules_vectors.json").read_text(encoding="utf-8")) == fresh, "ejecuta: python scripts/gen_rule_vectors.py"


def test_vectors_cover_the_critical_behaviours():
    d = json.loads((ROOT / "shared" / "rules_vectors.json").read_text(encoding="utf-8"))
    by = {s["name"]: s for s in d["scenarios"]}
    assert by["few_results"]["progress"] is None                      # poca evidencia: sin porcentaje
    assert by["clean_streak"]["streak_message"] == "Resolviste 6 ejercicios seguidos sin ayuda en Cantidad."
    assert by["open_question_only"]["results"]["a"]["closed"] is False
    assert by["improving_12"]["improve_message"] is not None and by["improving_12"]["progress"] is not None
    expected = [e["expected"] for e in d["evaluate"]]
    assert None in expected and True in expected and False in expected
