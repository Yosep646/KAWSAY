"""Pruebas de contratos reales: Ollama, solicitud de apoyo y activación del despachador.

El test HTTP usa un transporte aislado: no afirma que exista un modelo instalado en la escuela.
"""
import json
import threading
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app
from app.modules.ai.gateway import (
    AIGateway,
    AIProviderError,
    AIRequest,
    AITimeout,
    AIUnavailable,
    OllamaProvider,
)
from app.workers import auto_dispatch
from tests.test_sync_reto10 import _login, _published, _pull


def test_ollama_adapter_uses_actual_chat_contract_and_classifies_errors():
    captured = {}
    mode = {"value": "success"}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        if mode["value"] == "timeout":
            raise httpx.ReadTimeout("el modelo tardó demasiado")
        if mode["value"] == "offline":
            raise httpx.ConnectError("sin servicio local")
        if mode["value"] == "unavailable":
            return httpx.Response(503, text="datos privados: no exponer")
        if mode["value"] == "missing_model":
            return httpx.Response(404, text="modelo no instalado")
        if mode["value"] == "invalid":
            return httpx.Response(200, json={"message": []})
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "Busca primero qué datos tienes."}})

    provider = OllamaProvider("qwen2.5:3b", "http://127.0.0.1:11434/",
                              5, httpx.Client(transport=httpx.MockTransport(handler)))
    request = AIRequest("No reveles la respuesta", "Grado 4: ¿qué datos tengo?", max_tokens=64)
    result = AIGateway(provider, max_retries=0).generate(request)
    assert result.text == "Busca primero qué datos tienes."
    assert result.provider == "ollama" and result.model == "qwen2.5:3b"
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["body"]["stream"] is False
    assert captured["body"]["model"] == "qwen2.5:3b"
    assert captured["body"]["options"]["num_predict"] == 64
    assert captured["body"]["messages"] == [
        {"role": "system", "content": request.system},
        {"role": "user", "content": request.user},
    ]
    for value, exception in (
        ("offline", AIUnavailable), ("timeout", AITimeout),
        ("unavailable", AIUnavailable), ("missing_model", AIProviderError),
        ("invalid", AIProviderError),
    ):
        mode["value"] = value
        with pytest.raises(exception) as exc:
            provider.generate(request)
        assert "privados" not in str(exc.value)


def test_student_tutor_status_and_teacher_support_alert_respect_roles(w):
    teacher, other_teacher, _, (student,) = _published(w)
    auth = _login(w, student)
    status = w.c.get("/api/v1/tutor/status", headers=auth)
    assert status.status_code == 200
    assert status.json()["offline_hints_available"] is True
    assert status.json()["model_health_verified"] is False
    assert "ollama_base_url" not in str(status.json())
    assert w.c.get("/api/v1/tutor/status").status_code == 401

    assigned = _pull(w, auth)["tasks"][0]
    request = {"student_assignment_id": assigned["student_assignment_id"],
               "question_id": assigned["questions"][0]["id"], "step": 2}
    assert w.c.post("/api/v1/tutor/turn", headers=auth, json=request).status_code == 200
    own = w.c.get("/api/v1/tutor/help-requests", headers=teacher)
    assert own.status_code == 200
    assert len(own.json()) == 1
    assert own.json()[0]["student"] == student["display_name"]
    assert own.json()[0]["requires_teacher_decision"] is True
    assert w.c.get("/api/v1/tutor/help-requests", headers=other_teacher).json() == []
    assert w.c.get("/api/v1/tutor/help-requests", headers=auth).status_code == 403


def test_n8n_workflow_has_verified_hmac_and_failure_responses():
    path = Path(__file__).resolve().parents[2] / "automation/n8n/workflows/02_tutor_ia_alertas_educativas.json"
    workflow = json.loads(path.read_text(encoding="utf-8"))
    nodes = {n["name"]: n for n in workflow["nodes"]}
    assert workflow["active"] is False  # No se afirma que n8n esté conectado.
    assert nodes["Webhook KAWSAY Educativo"]["parameters"]["options"]["rawBody"] is True
    code = nodes["Validar HMAC y evento"]["parameters"]["jsCode"]
    assert "timingSafeEqual" in code and "sha256=" in code
    assert "JSON.stringify(item.json.body)" not in code  # No reconstruir mensaje firmado.
    assert "tutor.help.requested" in code and "student.support_flag.created" in code
    assert "student.display_name" not in code and "question_id" not in code
    assert nodes["Enviar aviso por SMTP"]["type"] == "n8n-nodes-base.emailSend"
    responses = {n["name"]: n["parameters"]["options"]["responseCode"]
                 for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.respondToWebhook"}
    assert responses["Responder enviado 200"] == 200
    assert responses["Responder SMTP pendiente 503"] == 503
    assert responses["Responder firma inválida 401"] == 401


def test_lifespan_runs_opted_in_automation_without_real_network(monkeypatch):
    settings = get_settings()
    called = threading.Event()
    monkeypatch.setattr(settings, "automation_auto_dispatch", True)
    monkeypatch.setattr(settings, "automation_webhook_url", "https://n8n.school.invalid/webhook/kawsay-educativo")
    monkeypatch.setattr(settings, "automation_webhook_secret", "local-test-secret-123456789")
    monkeypatch.setattr(auto_dispatch, "dispatch_once", lambda: (called.set() or {"delivered": 0, "failed": 0}))
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        assert called.wait(3), "El ciclo de auto-despacho no se activó tras startup."
    # TestClient cerró el lifespan: el worker se cancela limpiamente.
