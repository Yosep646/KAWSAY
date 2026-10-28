"""Selección pedagógica explicable. No modifica el grado matriculado ni publica tareas.

El riesgo ML es informativo; las evidencias por competencia gobiernan la recomendación.
El docente siempre debe revisar y aprobar las propuestas.
"""
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class CompetencyEvidence:
    competency_id: str
    grade: int
    attempts: int
    correct: int
    prerequisite_of: str | None = None

    def __post_init__(self):
        if not self.competency_id or not 1 <= self.grade <= 6:
            raise ValueError("Competencia o grado inválido")
        if self.attempts < 0 or not 0 <= self.correct <= self.attempts:
            raise ValueError("Evidencia inválida")


@dataclass(frozen=True)
class Recommendation:
    target_grade: int
    competency_id: str
    reason: str
    requires_teacher_approval: bool = True


def recommend(official_grade: int, target_competency: str,
              evidence: Sequence[CompetencyEvidence],
              ml_risk: float | None = None) -> Recommendation:
    """Recomienda refuerzo por competencia; nunca asigna ni publica.

    Las reglas son un PROTOTIPO, no umbrales pedagógicos validados.
    Se necesita >=5 respuestas por competencia para decidir.
    """
    if not 1 <= official_grade <= 6 or not target_competency:
        raise ValueError("Grado o competencia inválidos")
    if ml_risk is not None and not 0 <= ml_risk <= 1:
        raise ValueError("Riesgo inválido")
    current = next((e for e in evidence if e.competency_id == target_competency
                    and e.grade == official_grade), None)
    if current is None or current.attempts < 5:
        return Recommendation(official_grade, target_competency,
                              "Evidencia insuficiente: solicitar diagnóstico docente")
    if current.correct / current.attempts >= 0.8:
        return Recommendation(official_grade, target_competency,
                              "Dominio observado: continuar en el grado oficial")
    prerequisites = sorted(
        (e for e in evidence if e.prerequisite_of == target_competency
         and e.grade < official_grade and e.attempts >= 5
         and e.correct / e.attempts < 0.8),
        key=lambda e: e.grade,
    )
    if prerequisites:
        item = prerequisites[0]
        return Recommendation(item.grade, item.competency_id,
                              "Refuerzo de prerrequisito con evidencia de dificultad")
    return Recommendation(official_grade, target_competency,
                          "Dificultad observada: refuerzo guiado sin cambiar de grado")
