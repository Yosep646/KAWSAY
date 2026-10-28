"""Offline-capable, deterministic differentiation of teacher-authored arithmetic.

This is RULE AUTOMATION, not an ML model or a substitute for MINEDU approval.
The example in the teacher's source grade is preserved. Every other grade gets
different magnitude, language, scaffolding and (for higher grades) word problems.
All output stays in TEACHER_REVIEW and must be explicitly approved.
"""
import re
from dataclasses import dataclass

from app.modules.assignments.schemas import QuestionIn

RULE_VERSION = "math-grade-rules-v1"
_EXERCISE = re.compile(r"^\s*(\d{1,6})\s*([+\-×xX*÷/])\s*(\d{1,6})\s*(?:=\s*\??|\?)?\s*$")
_SYMBOL = {"x": "×", "X": "×", "*": "×", "/": "÷"}
_SUPPORTED = {"+", "-", "×", "÷"}
_MAGNITUDE: dict[int, tuple[int, int, int, int]] = {
    1: (2, 4, 1, 3),           # pequeñas cantidades concretas
    2: (12, 46, 8, 29),        # dos cifras
    3: (115, 450, 35, 185),   # centenas
    5: (1200, 6500, 750, 2550),
    6: (12000, 65000, 2500, 18500),
}
_HELP = {
    1: "Puedes contar con fichas o dibujar los objetos.",
    2: "Separa las decenas y unidades.",
    3: "Organiza las centenas, decenas y unidades.",
    4: "Resuelve por pasos y comprueba la operación.",
    5: "Explica el procedimiento y verifica el resultado.",
    6: "Elige una estrategia, justifica y comprueba el resultado.",
}


@dataclass(frozen=True)
class ArithmeticExample:
    left: int
    right: int
    symbol: str
    original: str


def parse_example(value: str) -> ArithmeticExample:
    """Only one explicit expression. No eval, implicit arithmetic or arbitrary text."""
    match = _EXERCISE.fullmatch(value)
    if match is None:
        raise ValueError("Escribe una operación completa, por ejemplo: 245 + 178")
    left, symbol, right = int(match[1]), _SYMBOL.get(match[2], match[2]), int(match[3])
    if symbol not in _SUPPORTED:
        raise ValueError("Operación no compatible")
    if symbol == "-" and left < right:
        raise ValueError("Utiliza una resta cuyo resultado no sea negativo")
    if symbol == "÷" and (right == 0 or left % right):
        raise ValueError("Utiliza una división exacta con divisor mayor que cero")
    return ArithmeticExample(left, right, symbol, f"{left} {symbol} {right}")


def _operands(ex: ArithmeticExample, grade: int, source_grade: int, n: int) -> tuple[int, int]:
    if grade == source_grade and n == 0:
        return ex.left, ex.right
    # Scale from the teacher's own example while respecting progressive magnitude.
    # Grade 4 is not special: *source_grade* can be any primary grade from 1 to 6.
    if grade == source_grade:
        left = max(1, ex.left + (n * max(1, ex.left // 7)))
        right = max(1, ex.right + (n * max(1, ex.right // 8)))
    else:
        lo_a, hi_a, lo_b, hi_b = _MAGNITUDE.get(grade, (120, 680, 45, 255)) if grade != 4 else (450, 1800, 170, 710)
        left = lo_a + (ex.left + n * 43) % (hi_a - lo_a + 1)
        right = lo_b + (ex.right + n * 23) % (hi_b - lo_b + 1)
    if ex.symbol == "-" and left < right:
        left, right = right + (1 if grade > 1 else 0), left
    if ex.symbol == "÷":
        # Exact quotients, grade 1 represented as equal sharing (not a formal long division).
        divisor = max(1, min(right, 2 + grade * 2))
        quotient = max(2, min(left, (4 if grade == 1 else 9 * (10 ** max(0, grade - 2)))))
        return divisor * quotient, divisor
    if ex.symbol == "×" and grade == 1:
        # Small equal groups; the conceptual task remains multiplication.
        return min(left, 4), min(right, 3)
    return left, right


def _answer(a: int, b: int, symbol: str) -> int:
    if symbol == "+":
        return a + b
    if symbol == "-":
        return a - b
    if symbol == "×":
        return a * b
    return a // b


def _prompt(a: int, b: int, op: str, grade: int, index: int, source: bool) -> str:
    if source and index == 0:
        return f"Resuelve la operación del docente: {a} {op} {b} = ?"
    if grade == 1:
        action = {
            "+": f"Hay {a} semillas y llegan {b} más. ¿Cuántas hay?",
            "-": f"Hay {a} semillas y se usan {b}. ¿Cuántas quedan?",
            "×": f"Hay {a} grupos con {b} semillas. ¿Cuántas hay?",
            "÷": f"Reparte {a} semillas en {b} grupos iguales. ¿Cuántas por grupo?",
        }
        return action[op]
    if grade == 2:
        return f"Calcula usando decenas y unidades: {a} {op} {b} = ?"
    if grade == 3:
        return f"Resuelve y comprueba: {a} {op} {b} = ?"
    if grade == 4:
        return f"Resuelve la operación y explica tus pasos: {a} {op} {b} = ?"
    if grade == 5:
        return f"En un registro de la comunidad aparece esta operación: {a} {op} {b}. ¿Cuál es el resultado?"
    return f"En una actividad de la comunidad se necesita calcular {a} {op} {b}. ¿Qué resultado corresponde y cómo lo compruebas?"


def generate_questions(example: ArithmeticExample, grade: int, source_grade: int) -> list[QuestionIn]:
    if not 1 <= grade <= 6 or not 1 <= source_grade <= 6:
        raise ValueError("La adaptación corresponde solamente a primaria de 1.º a 6.º")
    questions: list[QuestionIn] = []
    for i in range(3):
        left, right = _operands(example, grade, source_grade, i)
        result = _answer(left, right, example.symbol)
        questions.append(QuestionIn(
            type="NUMERIC",
            prompt=_prompt(left, right, example.symbol, grade, i, grade == source_grade),
            options=None,
            correct_answer={"value": result, "tolerance": 0},
            hints=[_HELP[grade]],
            explanation=f"{left} {example.symbol} {right} = {result}.",
            difficulty=(1 if grade < source_grade else 2 if grade == source_grade else 3),
        ))
    return questions


def instructions_for_grade(grade: int, source_grade: int, topic: str, objective: str) -> str:
    relation = "refuerzo" if grade < source_grade else "actividad base" if grade == source_grade else "ampliación"
    return (
        f"Matemática {grade}.º de primaria · {relation}. Tema: {topic}. "
        f"Objetivo: {objective}. {_HELP[grade]} "
        "Lee, resuelve las tres preguntas y revisa tu respuesta."
    )[:5000]
