import mimetypes

from fastapi.testclient import TestClient

from app.deploy import create_deployment_app


def test_deployment_serves_shell_worker_assets_and_keeps_api_404(tmp_path, monkeypatch):
    mimetypes.init()
    monkeypatch.setitem(mimetypes.types_map, ".webp", "application/octet-stream")
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>KAWSAY shell</html>", encoding="utf-8")
    (tmp_path / "sw.js").write_text("self.addEventListener('fetch', () => {});", encoding="utf-8")
    (tmp_path / "assets" / "app.js").write_text("const app='KAWSAY';", encoding="utf-8")
    (tmp_path / "assets" / "logo.webp").write_bytes(b"RIFF-test-WEBP")
    client = TestClient(create_deployment_app(tmp_path))
    for path in ("/", "/login", "/estudiante/descargada/example"):
        result = client.get(path)
        assert result.status_code == 200 and "KAWSAY shell" in result.text
        assert result.headers["cache-control"] == "no-store"
        assert "worker-src 'self'" in result.headers["content-security-policy"]
    worker = client.get("/sw.js")
    assert worker.status_code == 200 and worker.headers["content-type"].startswith("application/javascript")
    assert worker.headers["service-worker-allowed"] == "/"
    assert "connect-src 'self'" in worker.headers["content-security-policy"]
    assert "KAWSAY" in client.get("/assets/app.js").text
    assert client.get("/assets/logo.webp").headers["content-type"] == "image/webp"
    assert client.get("/api/v1/not-an-endpoint").status_code == 404
    assert client.get("/assets/not-a-file").status_code == 404
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json()["status"] == "ready"


def test_demo_bootstrap_requires_opt_in_and_is_idempotent(monkeypatch, db):
    from app.demo_bootstrap import bootstrap
    from app.modules.users.models import User

    monkeypatch.delenv("KAWSAY_DEMO_BOOTSTRAP", raising=False)
    bootstrap()
    assert db.query(User).count() == 0
    monkeypatch.setenv("KAWSAY_DEMO_BOOTSTRAP", "1")
    for role in ("ADMIN", "TEACHER"):
        monkeypatch.setenv(f"KAWSAY_DEMO_{role}_EMAIL", f"{role.lower()}@demo.pe")
        monkeypatch.setenv(f"KAWSAY_DEMO_{role}_PASSWORD", "Una-frase-ficticia-larga-2026!")
    bootstrap()
    bootstrap()
    assert db.query(User).count() == 2
    assert {row.role for row in db.query(User)} == {"ADMIN", "TEACHER"}
