"""Exporta secuencias SEUDONIMIZADAS de primaria para entrenar con datos REALES.

Se niega a exportar si no hay datos suficientes (no se entrena con tres alumnos de demostración).
No exporta nombre, código, DNI, ubicación ni idioma. El id de estudiante se reemplaza por HMAC con sal secreta.
Uso: DATABASE_URL=sqlite:///backend/data/kawsay.db ML_PSEUDONYM_SALT=... python -m ml.export_real --out ml/datasets/raw/real.jsonl
"""
import argparse
import hashlib
import hmac
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

MIN_STUDENTS = 200
MIN_SEQUENCES_WITH_ENOUGH_RESULTS = 150   # secuencias con >= HISTORY+HORIZON ejercicios cerrados


class InsufficientDataError(Exception):
    pass


def check_sufficiency(n_students: int, n_long_sequences: int, min_students: int = MIN_STUDENTS,
                      min_sequences: int = MIN_SEQUENCES_WITH_ENOUGH_RESULTS) -> None:
    if n_students < min_students or n_long_sequences < min_sequences:
        raise InsufficientDataError(
            f"Datos reales insuficientes para entrenar: {n_students} estudiantes (mín. {min_students}), "
            f"{n_long_sequences} secuencias largas (mín. {min_sequences}). No se exporta.")


def pseudonymize(student_id: str, salt: str) -> str:
    return "P" + hmac.new(salt.encode(), student_id.encode(), hashlib.sha256).hexdigest()[:16]


def export(database_url: str, salt: str, out: Path, min_students: int = MIN_STUDENTS,
           min_sequences: int = MIN_SEQUENCES_WITH_ENOUGH_RESULTS) -> dict:
    if len(salt) < 16:
        raise ValueError("ML_PSEUDONYM_SALT debe tener al menos 16 caracteres")
    from sqlalchemy import create_engine, text

    from ml.common import HISTORY, HORIZON, adaptive
    eng = create_engine(database_url)
    with eng.connect() as c:
        rows = c.execute(text("""
            SELECT a.student_user_id, a.competency_id, a.question_id, a.id, a.attempt_number,
                   a.is_correct, a.hints_used, a.effective_at, g.number
            FROM learning_attempts a
            JOIN student_profiles sp ON sp.user_id = a.student_user_id
            JOIN grades g ON g.id = sp.grade_id
            WHERE g.level = 'PRIMARIA' AND g.number BETWEEN 1 AND 6""")).fetchall()
    by_key: dict[tuple, list] = defaultdict(list)
    grade_of: dict[str, int] = {}
    for sid, comp, qid, aid, n, ok, h, at, grade in rows:
        at = at if isinstance(at, datetime) else datetime.fromisoformat(str(at))
        by_key[(sid, comp)].append(adaptive.AttemptFact(str(aid), str(qid), n, bool(ok), h, at))
        grade_of[sid] = grade
    seqs = []
    for (sid, comp), facts in by_key.items():
        res = sorted((r for r in adaptive.question_results(facts) if r.closed), key=lambda r: r.at)
        seqs.append({"student": pseudonymize(sid, salt), "grade": grade_of[sid],
                     "results": [{"score": r.score, "hints": r.hints, "wrong": r.wrong_attempts} for r in res]})
    n_students = len({s["student"] for s in seqs})
    n_long = sum(1 for s in seqs if len(s["results"]) >= HISTORY + HORIZON)
    check_sufficiency(n_students, n_long, min_students, min_sequences)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(s) for s in seqs), encoding="utf-8")
    return {"students": n_students, "sequences": len(seqs), "long_sequences": n_long}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("ml/datasets/raw/real.jsonl"))
    a = ap.parse_args()
    salt = os.environ.get("ML_PSEUDONYM_SALT", "")
    if len(salt) < 16:
        raise SystemExit("Define ML_PSEUDONYM_SALT (>=16 caracteres, secreta, fuera del repositorio)")
    print(export(os.environ["DATABASE_URL"], salt, a.out))
