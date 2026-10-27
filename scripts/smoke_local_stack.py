"""Smoke test no destructivo tras `docker compose up -d --build`.

Uso: python scripts/smoke_local_stack.py [http://127.0.0.1:8080]
"""
import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080").rstrip("/")


def get(path: str):
    req = Request(BASE + path, headers={"Accept": "application/json" if path.startswith("/api/") else "*/*"})
    try:
        with urlopen(req, timeout=10) as res:
            return res.status, res.headers, res.read().decode("utf-8")
    except HTTPError as exc:
        return exc.code, exc.headers, exc.read().decode("utf-8")


def main():
    for path in ("/", "/admin", "/docente", "/estudiante"):
        code, headers, body = get(path)
        assert code == 200 and "<html" in body.lower(), (path, code, body[:100])
        print("PASS página", path)
    for path in ("/health", "/ready"):
        code, headers, body = get(path)
        assert code == 200 and json.loads(body)["status"] in ("ok", "ready"), (path, code, body)
        print("PASS backend", path)
    code, headers, body = get("/api/v1/auth/me")
    assert code == 401 and headers.get("content-type", "").startswith("application/json"), (code, body[:100])
    assert headers.get("x-content-type-options") == "nosniff", "Cabecera de seguridad ausente"
    print("PASS API protegida y conectada por Nginx")
    print("Smoke test aprobado: web + API + base (ready). NO verifica login real ni offline.")


if __name__ == "__main__":
    main()
