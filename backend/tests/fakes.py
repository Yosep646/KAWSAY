"""Proveedores de IA FALSOS: existen SOLO para pruebas (nunca se usan en producción)."""
import json
import re

from app.modules.ai.gateway import AIGateway, AIRequest, AIResponse, AITimeout, AIUnavailable, get_gateway


class FakeProvider:
    name, model = "fake", "fake-1"

    def __init__(self, handler):
        self.handler, self.calls = handler, []

    def generate(self, req: AIRequest) -> AIResponse:
        self.calls.append(req)
        out = self.handler(req)
        return AIResponse(text=out, provider=self.name, model=self.model)


def _field(req: AIRequest, label: str) -> str:
    return re.search(rf"^{label}: (.*)$", req.user, re.M).group(1).strip()


def content_for(req: AIRequest, **over) -> str:
    grade = int(re.search(r"Grado: (\d)", req.user).group(1))
    topic, subj, comp = _field(req, "Tema"), _field(req, "Área"), _field(req, "Competencia")
    data = {"echo": {"grade": grade, "subject": subj, "competency": comp, "topic": topic},
            "title": f"{topic} para {grade}.º",
            "instructions": f"Lee con calma. Trabajaremos el tema {topic}. Elige la respuesta correcta.",
            "questions": [{"type": "MULTIPLE_CHOICE", "prompt": f"Ejercicio {i + 1} de {topic}: ¿cuál es mayor?",
                           "options": ["menor", "mayor"], "correct_answer": {"index": 1},
                           "hints": ["Compara con calma", "Usa material concreto"], "explanation": "Lo mayor tiene más.",
                           "difficulty": 1} for i in range(3)]}
    data.update(over)
    return json.dumps(data, ensure_ascii=False)


def good(req):
    return content_for(req)


def raising(exc):
    def h(_req):
        raise exc
    return h


def install(app, provider, **kw):
    gw = AIGateway(provider, **({"max_retries": 0} | kw))
    app.dependency_overrides[get_gateway] = lambda: gw
    return gw


__all__ = ["AITimeout", "AIUnavailable", "FakeProvider", "content_for", "good", "install", "raising"]
