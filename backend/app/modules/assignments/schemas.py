from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuestionIn(_In):
    type: Literal["MULTIPLE_CHOICE", "NUMERIC", "SHORT_TEXT"]
    prompt: str = Field(min_length=3, max_length=2000)
    options: list[Annotated[str, Field(min_length=1, max_length=300)]] | None = Field(default=None, max_length=6)
    correct_answer: dict[str, Any]
    hints: list[Annotated[str, Field(min_length=1, max_length=500)]] = Field(default_factory=list, max_length=5)
    explanation: str | None = Field(default=None, max_length=2000)
    difficulty: int = Field(default=2, ge=1, le=3)

    @model_validator(mode="after")
    def _by_type(self) -> "QuestionIn":
        ca = self.correct_answer
        if self.type == "MULTIPLE_CHOICE":
            idx = ca.get("index")
            if not self.options or len(self.options) < 2 or not isinstance(idx, int) or not 0 <= idx < len(self.options):
                raise ValueError("MULTIPLE_CHOICE requiere >=2 opciones y correct_answer.index válido")
        elif self.type == "NUMERIC":
            if self.options is not None or not isinstance(ca.get("value"), int | float) or isinstance(ca.get("value"), bool):
                raise ValueError("NUMERIC requiere correct_answer.value numérico y sin opciones")
            tol = ca.get("tolerance", 0)
            if not isinstance(tol, int | float) or tol < 0:
                raise ValueError("tolerance inválida")
        else:
            acc = ca.get("accepted")
            if self.options is not None or not isinstance(acc, list) or not acc or not all(isinstance(x, str) and x for x in acc):
                raise ValueError("SHORT_TEXT requiere correct_answer.accepted (lista de textos)")
        return self


class QuestionsIn(_In):
    questions: list[QuestionIn] = Field(min_length=1, max_length=30)
