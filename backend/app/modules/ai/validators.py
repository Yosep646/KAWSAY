"""OutputValidator (forma/seguridad) y CurriculumValidator (fidelidad al contexto curricular). Sin IA: reglas."""
import json
import re
import unicodedata
from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.modules.assignments.schemas import QuestionIn

URL_RE = re.compile(r"(https?://|www\.)", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\d[\d\s-]{7,}\d")
BANNED = ("suicid", "matar", "porn", "sexo", "droga", "arma de fuego")
STOPWORDS = {"para", "como", "entre", "sobre", "desde", "hasta", "cada", "esta", "este", "estos", "estas", "tiene",
             "tienen", "pueden", "puede", "donde", "cuando", "segun", "mediante", "usando", "del", "las", "los", "con"}
MAX_WORDS_PER_SENTENCE = {1: 10, 2: 10, 3: 14, 4: 14, 5: 18, 6: 18}


class OutputInvalid(Exception):  # noqa: N818
    pass


class Echo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grade: int
    subject: str
    competency: str
    topic: str


class AIContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    echo: Echo
    title: str = Field(min_length=2, max_length=300)
    instructions: str = Field(min_length=5, max_length=5000)
    questions: list[QuestionIn] = Field(min_length=3, max_length=10)


@dataclass
class Context:
    grade_level: str
    grade_number: int
    subject: str
    competency: str
    topic: str
    objective: str
    other_subjects: list[str] = field(default_factory=list)


def norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in t if not unicodedata.combining(c))


def _all_text(c: AIContent) -> str:
    return " ".join([c.title, c.instructions] + [q.prompt for q in c.questions] + [o for q in c.questions for o in (q.options or [])])


def parse_output(raw: str, ctx: Context) -> AIContent:
    """OutputValidator: no se confía en el modelo; forma, límites y contenido inapropiado."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S).strip()
    try:
        content = AIContent.model_validate(json.loads(text))
    except (ValueError, ValidationError) as exc:
        raise OutputInvalid("La salida no cumple el formato esperado") from exc
    blob = _all_text(content)
    if URL_RE.search(blob) or EMAIL_RE.search(blob) or PHONE_RE.search(blob):
        raise OutputInvalid("La salida contiene enlaces, correos o teléfonos")
    nb = norm(blob)
    if any(b in nb for b in BANNED):
        raise OutputInvalid("La salida contiene contenido no apropiado para estudiantes")
    limit = MAX_WORDS_PER_SENTENCE.get(ctx.grade_number, 25) if ctx.grade_level == "PRIMARIA" else 25
    texts = [content.instructions] + [q.prompt for q in content.questions]
    sentences = [s for t in texts for s in re.split(r"[.!?¿?\n]+", t) if s.strip()]
    lengths = [len(s.split()) for s in sentences] or [0]
    avg, longest = sum(lengths) / len(lengths), max(lengths)
    if avg > limit or longest > limit * 1.6:
        raise OutputInvalid(f"El lenguaje es demasiado complejo para el grado (promedio {avg:.0f}, máx. {longest} palabras/oración)")
    return content


def _keywords(*texts: str) -> set[str]:
    words = set()
    for t in texts:
        words |= {w for w in re.findall(r"[a-z]{4,}", norm(t)) if w not in STOPWORDS}
    return words


def curriculum_check(content: AIContent, ctx: Context) -> list[str]:
    """CurriculumValidator: devuelve motivos de desvío ([] = fiel al contexto). Nunca publica nada."""
    reasons = []
    e = content.echo
    if e.grade != ctx.grade_number:
        reasons.append(f"grado declarado {e.grade} ≠ {ctx.grade_number}")
    for label, got, want in (("área", e.subject, ctx.subject), ("competencia", e.competency, ctx.competency),
                             ("tema", e.topic, ctx.topic)):
        if norm(got).strip() != norm(want).strip():
            reasons.append(f"{label} declarada no coincide con la planificación")
    blob = norm(_all_text(content))
    kws = _keywords(ctx.topic, ctx.objective)
    hits = {k for k in kws if k in blob}
    if kws and len(hits) < min(2, len(kws)):
        reasons.append("el contenido no menciona los términos centrales del tema/objetivo")
    for other in ctx.other_subjects:
        if norm(other) in blob:
            reasons.append(f"menciona otra área curricular: {other}")
    return reasons
