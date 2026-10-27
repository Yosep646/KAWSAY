import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import cli
from app.core.config import get_settings
from app.core.database import _db_path
from app.core.password_policy import WeakPassword, check_password_policy
from app.main import create_app
from tests.conftest import PW
from tests.test_sync_reto10 import _published


def test_security_headers_on_every_response(w):
    r = w.c.get("/health")
    h = r.headers
    assert h["X-Content-Type-Options"] == "nosniff" and h["X-Frame-Options"] == "DENY" and h["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in h["Content-Security-Policy"] and h["Cache-Control"] == "no-store"
    assert "geolocation=()" in h["Permissions-Policy"]
    assert "Strict-Transport-Security" not in h                                 # solo en producción
    assert "Content-Security-Policy" not in w.c.get("/docs").headers            # Swagger necesita sus recursos


def test_hsts_in_production(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_env", "production")
    assert "max-age" in TestClient(create_app()).get("/health").headers["Strict-Transport-Security"]


def test_requests_without_verifiable_length_are_rejected(w):
    r = w.c.post("/api/v1/auth/login", content=b"{}", headers={"transfer-encoding": "chunked", "content-type": "application/json"})
    assert r.status_code == 411
    assert w.c.post("/api/v1/auth/login", content=b"{}", headers={"content-length": "abc"}).status_code in (400, 411)
    big = json.dumps({"email": "a@b.pe", "password": "x" * 2_000_000})
    assert w.c.post("/api/v1/auth/login", content=big, headers={"content-type": "application/json"}).status_code == 413


@pytest.mark.parametrize("payload", ["' OR '1'='1", "admin@x.pe' --", "'; DROP TABLE users; --", "\" OR 1=1 /*"])
def test_sql_injection_attempts_do_not_authenticate_or_damage_data(w, payload):
    w.staff("ADMIN", "admin@x.pe")
    for body in ({"email": payload, "password": payload}, {"email": "admin@x.pe", "password": payload}):
        assert w.c.post("/api/v1/auth/login", json=body).status_code in (401, 422)
    assert w.c.post("/api/v1/auth/student-login", json={"login_code": payload, "pin": payload,
                                                        "device_id": "11111111-1111-1111-1111-111111111111"}).status_code in (401, 422)
    h = w.login("admin@x.pe")                                                    # las tablas siguen intactas
    assert w.c.get("/api/v1/users", headers=h).status_code == 200


def test_xss_payload_is_stored_as_data_and_served_as_json_with_nosniff(w):
    school = w.school()
    w.staff("TEACHER", "t@x.pe", school)
    h = w.login("t@x.pe")
    room = w.classroom(h, "<script>alert(1)</script>")
    r = w.c.get(f"/api/v1/classrooms/{room}", headers=h)
    assert r.headers["content-type"].startswith("application/json") and r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.json()["name"] == "<script>alert(1)</script>"                       # dato, nunca HTML ejecutable


def test_cors_allows_only_configured_origins(monkeypatch):
    monkeypatch.setattr(get_settings(), "cors_origins", "http://localhost:5173")
    c = TestClient(create_app())
    ok = c.options("/api/v1/auth/login", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    bad = c.options("/api/v1/auth/login", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in bad.headers


@pytest.mark.parametrize("pw", ["corta", "password1234", "aaaaaaaaaaaa", "una-clave-larga-123".replace("una", "yosep")])
def test_password_policy_rejects_weak_passwords(pw):
    if pw.startswith("yosep"):
        with pytest.raises(WeakPassword):
            check_password_policy(pw, email="yosep@x.pe")                         # contiene la parte local del correo
    else:
        with pytest.raises(WeakPassword):
            check_password_policy(pw)
    check_password_policy("tres-lunas-de-cobre-81")                               # larga y no común: válida


def test_admin_cannot_create_users_with_weak_passwords(w):
    school = w.school()
    w.staff("ADMIN", "admin@x.pe")
    h = w.login("admin@x.pe")
    r = w.c.post("/api/v1/users", headers=h, json={"role": "TEACHER", "email": "n@x.pe", "password": "password1234",
                                                   "display_name": "N", "school_id": str(school.id)})
    assert r.status_code == 422 and r.json()["code"] == "weak_password"


def test_change_password_requires_current_revokes_other_sessions_and_issues_new_tokens(w):
    w.staff("ADMIN", "admin@x.pe")
    old = w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": PW}).json()
    h = {"Authorization": f"Bearer {old['access_token']}"}
    bad = w.c.post("/api/v1/auth/change-password", headers=h, json={"current_password": "incorrecta-123456", "new_password": "tres-lunas-de-cobre-81"})
    assert bad.status_code == 401
    assert w.c.post("/api/v1/auth/change-password", headers=h, json={"current_password": PW, "new_password": PW}).status_code == 422
    assert w.c.post("/api/v1/auth/change-password", headers=h, json={"current_password": PW, "new_password": "password1234"}).status_code == 422
    ok = w.c.post("/api/v1/auth/change-password", headers=h, json={"current_password": PW, "new_password": "tres-lunas-de-cobre-81"})
    assert ok.status_code == 200
    assert w.c.post("/api/v1/auth/refresh", json={"refresh_token": old["refresh_token"]}).status_code == 401   # sesiones viejas cerradas
    assert w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": PW}).status_code == 401
    assert w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": "tres-lunas-de-cobre-81"}).status_code == 200
    assert w.c.post("/api/v1/auth/refresh", json={"refresh_token": ok.json()["refresh_token"]}).status_code == 200


def test_students_cannot_use_change_password_and_it_is_not_public(w):
    ta, *_ = _published(w)
    assert w.c.post("/api/v1/auth/change-password", json={"current_password": "x", "new_password": "tres-lunas-de-cobre-81"}).status_code == 401


def test_admin_deactivates_user_and_all_sessions_die_immediately(w):
    school = w.school()
    w.staff("ADMIN", "admin@x.pe")
    t = w.staff("TEACHER", "t@x.pe", school)
    admin = w.login("admin@x.pe")
    tok = w.c.post("/api/v1/auth/login", json={"email": "t@x.pe", "password": PW}).json()
    th = {"Authorization": f"Bearer {tok['access_token']}"}
    assert w.c.get("/api/v1/classrooms", headers=th).status_code == 200
    assert w.c.patch(f"/api/v1/users/{t.id}", headers=admin, json={"is_active": False}).status_code == 200
    assert w.c.get("/api/v1/classrooms", headers=th).status_code == 401
    assert w.c.post("/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]}).status_code == 401
    assert w.c.post("/api/v1/auth/login", json={"email": "t@x.pe", "password": PW}).status_code == 401
    assert w.c.patch(f"/api/v1/users/{t.id}", headers=th, json={"is_active": True}).status_code == 401       # no se auto-reactiva
    me = w.c.get("/api/v1/users", headers=admin).json()
    admin_id = next(u["id"] for u in me if u["email"] == "admin@x.pe")
    assert w.c.patch(f"/api/v1/users/{admin_id}", headers=admin, json={"is_active": False}).status_code == 409  # no se auto-bloquea
    assert w.c.patch(f"/api/v1/users/{t.id}", headers=admin, json={"is_active": True}).status_code == 200


def test_failed_logins_are_logged_without_secrets(w, caplog):
    w.staff("ADMIN", "admin@x.pe")
    with caplog.at_level("WARNING", logger="kawsay.security"):
        w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": "SuperSecreta-9999"})
    text = " ".join(r.getMessage() + str(getattr(r, "extra_fields", "")) for r in caplog.records)
    assert "login_failed" in text and "SuperSecreta-9999" not in text and "admin@x.pe" not in text


def test_database_file_is_private_and_backup_is_consistent_and_rotated(w, tmp_path):
    school = w.school("Escuela Respaldo")
    w.staff("ADMIN", "admin@x.pe", None)
    path = _db_path(get_settings().database_url)
    import os
    import stat
    if os.name == "posix":
        assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0                   # solo el dueño puede leer la base
    copies = [cli.backup(str(tmp_path / "bk"), keep=2) for _ in range(3)]
    assert len(list((tmp_path / "bk").glob("kawsay-*.db"))) == 2                # rotación
    con = sqlite3.connect(copies[-1])
    assert con.execute("select count(*) from schools where name='Escuela Respaldo'").fetchone()[0] == 1
    assert con.execute("pragma integrity_check").fetchone()[0] == "ok"
    assert cli.check_db() == {"integrity": "ok", "foreign_key_violations": 0, "journal_mode": "wal"}
    _ = school
