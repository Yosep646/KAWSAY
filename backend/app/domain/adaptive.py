"""Reglas pedagógicas deterministas y auditables (sin I/O, sin IA).

Unidad de evidencia = resultado de un EJERCICIO (pregunta) del estudiante, derivado de sus intentos.
Todo número relevante vive en RULES (versionado) para poder auditarlo y ajustarlo con docentes.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

METHOD_VERSION = "progress-v1"
RULE_SUPPORT_ID = "R-SUP-001"
RULE_SUPPORT_VERSION = "1"

RULES = {
    "max_attempts_per_question": 3,   # tras 3 intentos fallidos el ejercicio se considera cerrado
    "score_clean": 1.0,               # correcto sin pistas ni errores previos
    "score_some_help": 0.7,           # correcto con 1 pista o 1 error previo
    "score_much_help": 0.4,           # correcto con >=2 pistas o >=2 errores previos
    "score_wrong": 0.0,               # cerrado sin acierto
    "difficulty_score_max": 0.4,      # un ejercicio con score <= 0.4 "presenta dificultad"
    "progress_window": 20,            # últimos K ejercicios cerrados
    "progress_decay": 0.9,            # peso = decay ** antigüedad (0 = más reciente)
    "progress_min_evidence": 5,       # menos que esto => sin porcentaje ("sin evidencia suficiente")
    "support_window": 5,              # últimos N ejercicios cerrados de la competencia
    "support_min_difficult": 4,       # >= M con dificultad => Support Flag
    "level_refuerzo_below": 0.5,
    "level_desafio_above": 0.85,
}


@dataclass(frozen=True)
class AttemptFact:
    attempt_id: str
    question_id: str
    attempt_number: int
    is_correct: bool
    hints_used: int
    effective_at: datetime


@dataclass(frozen=True)
class QuestionResult:
    question_id: str
    score: float
    correct: bool
    closed: bool
    attempts: int
    wrong_attempts: int
    hints: int
    at: datetime


@dataclass
class DifficultyFinding:
    rule_id: str
    rule_version: str
    window: int
    difficult: int
    hints_total: int
    wrong_attempts_total: int
    distinct_days: int
    results: list[dict] = field(default_factory=list)


def question_results(attempts: list[AttemptFact]) -> list[QuestionResult]:
    by_q: dict[str, list[AttemptFact]] = defaultdict(list)
    for a in attempts:
        by_q[a.question_id].append(a)
    out = []
    for qid, items in by_q.items():
        items.sort(key=lambda a: (a.attempt_number, a.effective_at))
        correct = any(a.is_correct for a in items)
        wrong = sum(1 for a in items if not a.is_correct)
        hints = sum(a.hints_used for a in items)
        closed = correct or len(items) >= RULES["max_attempts_per_question"]
        if not correct:
            score = RULES["score_wrong"]
        elif hints >= 2 or wrong >= 2:
            score = RULES["score_much_help"]
        elif hints == 1 or wrong == 1:
            score = RULES["score_some_help"]
        else:
            score = RULES["score_clean"]
        out.append(QuestionResult(qid, score, correct, closed, len(items), wrong, hints,
                                  max(a.effective_at for a in items)))
    return out


def _closed_recent_first(results: list[QuestionResult]) -> list[QuestionResult]:
    return sorted((r for r in results if r.closed), key=lambda r: (r.at, r.question_id), reverse=True)


def compute_progress(results: list[QuestionResult]) -> tuple[float | None, int]:
    """Media ponderada (más peso a lo reciente). None si hay poca evidencia: nunca se inventa un %."""
    recent = _closed_recent_first(results)[: int(RULES["progress_window"])]
    if len(recent) < RULES["progress_min_evidence"]:
        return None, len(recent)
    weights = [RULES["progress_decay"] ** i for i in range(len(recent))]
    score = sum(w * r.score for w, r in zip(weights, recent, strict=True)) / sum(weights)
    return round(score, 4), len(recent)


def level_for(score: float | None) -> str | None:
    if score is None:
        return None
    if score < RULES["level_refuerzo_below"]:
        return "REFUERZO"
    if score > RULES["level_desafio_above"]:
        return "DESAFIO"
    return "ESPERADO"


def difficulty_recommendation(score: float | None, evidence_count: int) -> dict:
    """Sugerencia orientativa para elegir ejercicios aprobados por el docente."""
    if score is None or evidence_count < RULES["progress_min_evidence"]:
        return {"action": "INSUFFICIENT_EVIDENCE", "suggested_difficulty": None,
                "reason": "Se necesitan más ejercicios cerrados antes de sugerir un cambio."}
    level = level_for(score)
    if level == "REFUERZO":
        return {"action": "LOWER", "suggested_difficulty": 1,
                "reason": "El progreso reciente sugiere practicar con ejercicios de refuerzo."}
    if level == "DESAFIO":
        return {"action": "RAISE", "suggested_difficulty": 3,
                "reason": "El progreso reciente sugiere probar ejercicios de mayor desafío."}
    return {"action": "MAINTAIN", "suggested_difficulty": 2,
            "reason": "El progreso reciente sugiere mantener la dificultad esperada."}


def detect_difficulty(results: list[QuestionResult]) -> DifficultyFinding | None:
    window = int(RULES["support_window"])
    recent = _closed_recent_first(results)[:window]
    if len(recent) < window:
        return None  # sin evidencia suficiente no se alerta
    difficult = [r for r in recent if r.score <= RULES["difficulty_score_max"]]
    if len(difficult) < RULES["support_min_difficult"]:
        return None
    return DifficultyFinding(
        rule_id=RULE_SUPPORT_ID, rule_version=RULE_SUPPORT_VERSION, window=window, difficult=len(difficult),
        hints_total=sum(r.hints for r in recent), wrong_attempts_total=sum(r.wrong_attempts for r in recent),
        distinct_days=len({r.at.date() for r in recent}),
        results=[{"question_id": r.question_id, "score": r.score, "correct": r.correct, "attempts": r.attempts,
                  "hints": r.hints, "at": r.at.isoformat()} for r in recent])


def evaluate_answer(qtype: str, correct_answer: dict, answer: dict) -> bool | None:
    """Corrige en servidor (el cliente no es confiable). None = respuesta mal formada."""
    try:
        if qtype == "MULTIPLE_CHOICE":
            idx = answer.get("index")
            return None if not isinstance(idx, int) or isinstance(idx, bool) else idx == correct_answer["index"]
        if qtype == "NUMERIC":
            v = answer.get("value")
            if not isinstance(v, int | float) or isinstance(v, bool):
                return None
            return abs(float(v) - float(correct_answer["value"])) <= float(correct_answer.get("tolerance", 0))
        if qtype == "SHORT_TEXT":
            t = answer.get("text")
            if not isinstance(t, str):
                return None
            norm = " ".join(t.casefold().split())
            return norm in {" ".join(a.casefold().split()) for a in correct_answer["accepted"]}
    except (KeyError, TypeError, ValueError):
        return None
    return None


# ---------------------------------------------------------------- fortalezas y motivación (evidencia real)
def _closed_asc(results: list[QuestionResult]) -> list[QuestionResult]:
    return sorted((r for r in results if r.closed), key=lambda r: (r.at, r.question_id))


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def detect_strengths(results: list[QuestionResult]) -> list[dict]:
    """Patrones positivos observables. No son diagnósticos ni etiquetas de capacidad."""
    c = _closed_asc(results)
    out: list[dict] = []
    if len(c) >= 10:
        last5, prev5 = c[-5:], c[-10:-5]
        h_last, h_prev = _mean([r.hints for r in last5]), _mean([r.hints for r in prev5])
        if h_prev >= 1.0 and h_prev - h_last >= 1.0:
            out.append({"rule_id": "S-HINTS-001", "name": "menos_pistas",
                        "evidence": {"hints_per_exercise_before": round(h_prev, 2), "hints_per_exercise_now": round(h_last, 2)}})
        s_last, s_prev = _mean([r.score for r in last5]), _mean([r.score for r in prev5])
        if s_last - s_prev >= 0.2 and s_last >= 0.7:
            out.append({"rule_id": "S-IMPROVE-001", "name": "mejora_sostenida",
                        "evidence": {"score_before": round(s_prev, 2), "score_now": round(s_last, 2)}})
        score, count = compute_progress(results)
        if score is not None and score > RULES["level_desafio_above"] and count >= 10:
            out.append({"rule_id": "S-MASTERY-001", "name": "dominio_creciente",
                        "evidence": {"score": score, "evidence_count": count}})
    streak = 0
    for r in reversed(c):
        if r.score == RULES["score_clean"]:
            streak += 1
        else:
            break
    if streak >= 3:
        out.append({"rule_id": "S-STREAK-001", "name": "racha_sin_ayuda", "evidence": {"consecutive_clean": streak}})
    return out


def motivation_messages(results: list[QuestionResult], competency_name: str) -> list[str]:
    """Mensajes basados en datos reales; si no hay evidencia no hay mensaje."""
    c = _closed_asc(results)
    msgs: list[str] = []
    days: dict = {}
    for r in c:
        days.setdefault(r.at.date(), []).append(r)
    keys = sorted(days)
    if len(keys) >= 2:
        last, prev = _mean([r.hints for r in days[keys[-1]]]), _mean([r.hints for r in days[keys[-2]]])
        if prev > last:
            msgs.append(f"En tu última sesión necesitaste menos pistas que en la anterior ({last:.1f} frente a {prev:.1f} por ejercicio).")
    streak = 0
    for r in reversed(c):
        if r.score != RULES["score_clean"]:
            break
        streak += 1
    if streak >= 3:
        msgs.append(f"Resolviste {streak} ejercicios seguidos sin ayuda en {competency_name}.")
    if len(c) >= 10:
        a, b = _mean([r.score for r in c[-10:-5]]), _mean([r.score for r in c[-5:]])
        if b - a >= 0.2:
            msgs.append(f"Tu precisión mejoró en {competency_name}: de {round(a * 100)} % a {round(b * 100)} %.")
    return msgs
