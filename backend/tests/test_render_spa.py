"""Verificaciones de enrutamiento del despliegue monolítico React+FastAPI."""
from fastapi.testclient import TestClient

from app.main import create_app


def test_render_spa_routes_and_api_isolation(monkeypatch, tmp_path):
    (tmp_path / "index.html").write_text("<html>KAWSAY AI</html>", encoding="utf-8")
    (tmp_path / "sw.js").write_text("self.addEventListener('install',()=>{})", encoding="utf-8")
    # JPEG real usado en el banner del administrador (no HTML de React).
    hero_bytes = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"KAWSAY" + bytes([0xFF, 0xD9])
    (tmp_path / "kawsay-hero-rural.jpg").write_bytes(hero_bytes)
    (tmp_path / "kawsay-diversidad-fondo.jpg").write_bytes(hero_bytes)
    (tmp_path / "kawsay-login-encuadre-desktop.jpg").write_bytes(hero_bytes)
    (tmp_path / "kawsay-login-encuadre-mobile.jpg").write_bytes(hero_bytes)
    (tmp_path / "kawsay-reference-hero.jpg").write_bytes(hero_bytes)
    (tmp_path / "kawsay-reference-mobile.jpg").write_bytes(hero_bytes)
    # Los fondos nuevos de KAWSAY deben servirse como imagen, no index.html.
    webp_bytes = b"RIFF" + bytes(4) + b"WEBPVP8 " + b"KAWSAY"
    (tmp_path / "kawsay-fondo-responsive-20261028.webp").write_bytes(webp_bytes)
    (tmp_path / "kawsay-fondo-final.jpg").write_bytes(hero_bytes)
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index.js").write_text("console.log('KAWSAY')", encoding="utf-8")
    monkeypatch.setenv("KAWSAY_SERVE_WEB_DIR", str(tmp_path))

    with TestClient(create_app()) as client:
        for route in ("/", "/admin", "/docente", "/estudiante", "/estudiante/actividades"):
            response = client.get(route)
            assert response.status_code == 200
            assert "KAWSAY AI" in response.text
            assert response.headers["cache-control"] == "no-store"
            # CSP HTML permite cargar JS/CSS de React; el middleware no debe borrarla.
            assert "script-src 'self'" in response.headers["content-security-policy"]
            assert "style-src 'self' 'unsafe-inline'" in response.headers["content-security-policy"]
        assert client.get("/sw.js").status_code == 200
        hero = client.get("/kawsay-hero-rural.jpg")
        assert hero.status_code == 200
        assert hero.headers["content-type"].startswith("image/jpeg")
        assert hero.content == hero_bytes
        assert hero.headers["cache-control"] == "no-store"
        multicultural = client.get("/kawsay-diversidad-fondo.jpg")
        assert multicultural.status_code == 200
        assert multicultural.headers["content-type"].startswith("image/jpeg")
        assert multicultural.content == hero_bytes
        for name in ("kawsay-login-encuadre-desktop.jpg", "kawsay-login-encuadre-mobile.jpg",
                     "kawsay-reference-hero.jpg", "kawsay-reference-mobile.jpg"):
            picture = client.get(f"/{name}")
            assert picture.status_code == 200
            assert picture.headers["content-type"].startswith("image/jpeg")
            assert picture.content == hero_bytes
        for name, mime, data in (
            ("kawsay-fondo-responsive-20261028.webp", "image/webp", webp_bytes),
            ("kawsay-fondo-final.jpg", "image/jpeg", hero_bytes),
        ):
            picture = client.get(f"/{name}")
            assert picture.status_code == 200
            assert picture.headers["content-type"].startswith(mime)
            assert picture.content == data
            assert picture.headers["x-content-type-options"] == "nosniff"
            assert picture.headers["cache-control"] == "no-store"
        # Si falta una fotografía, nunca devolver HTML con código 200.
        assert client.get("/kawsay-imagen-inexistente.webp").status_code == 404
        assert client.get("/assets/index.js").status_code == 200
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/api/v1/una-ruta-inexistente").status_code == 404


def test_render_static_missing_build_fails_early(monkeypatch, tmp_path):
    monkeypatch.setenv("KAWSAY_SERVE_WEB_DIR", str(tmp_path))
    try:
        create_app()
    except RuntimeError as exc:
        assert "Falta frontend compilado" in str(exc)
    else:
        raise AssertionError("Debería fallar si React todavía no se compiló")
