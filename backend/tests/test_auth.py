from datetime import timedelta

import jwt

from app.core.config import get_settings
from app.core.rate_limit import reset_rate_limits
from app.modules.users.models import User
from tests.conftest import PW, new_device


def test_login_and_me(w):
    w.staff("ADMIN", "admin@x.pe")
    r = w.c.post("/api/v1/auth/login", json={"email": "ADMIN@x.pe", "password": PW})
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["role"] == "ADMIN" and "password" not in r.text
    me = w.c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json()["role"] == "ADMIN"


def test_password_stored_hashed(w, db):
    w.staff("ADMIN", "admin@x.pe")
    u = db.query(User).one()
    assert u.password_hash.startswith("$argon2") and PW not in u.password_hash


def test_wrong_password_and_unknown_user_same_error(w):
    w.staff("ADMIN", "admin@x.pe")
    a = w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": "mala"})
    b = w.c.post("/api/v1/auth/login", json={"email": "nadie@x.pe", "password": "mala"})
    assert a.status_code == b.status_code == 401
    assert a.json()["message"] == b.json()["message"]


def test_account_lockout(w):
    w.staff("ADMIN", "admin@x.pe")
    for _ in range(get_settings().max_failed_logins):
        w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": "mala"})
    ok = w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": PW})
    assert ok.status_code == 401  # bloqueada aunque la clave sea correcta


def test_rate_limit(w):
    reset_rate_limits()
    get_settings().login_rate_limit_per_minute = 3
    codes = [w.c.post("/api/v1/auth/login", json={"email": "a@x.pe", "password": "x"}).status_code
             for _ in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]


def test_missing_tampered_expired_tokens_rejected(w):
    w.staff("ADMIN", "admin@x.pe")
    assert w.c.get("/api/v1/auth/me").status_code == 401
    h = w.login("admin@x.pe")
    tok = h["Authorization"].split()[1]
    assert w.c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tok}x"}).status_code == 401
    forged = jwt.encode({"sub": "x", "typ": "access", "iss": "kawsay", "exp": 9999999999}, "otra-clave" * 5,
                        algorithm="HS256")
    assert w.c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    alg_none = jwt.encode({"sub": "x", "typ": "access", "iss": "kawsay", "exp": 9999999999}, None,
                          algorithm="none")
    assert w.c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {alg_none}"}).status_code == 401
    expired = jwt.encode({"sub": "x", "typ": "access", "iss": "kawsay", "exp": 1}, get_settings().jwt_secret,
                         algorithm="HS256")
    assert w.c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_refresh_rotation_and_reuse_detection(w):
    w.staff("ADMIN", "admin@x.pe")
    t1 = w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": PW}).json()
    t2 = w.c.post("/api/v1/auth/refresh", json={"refresh_token": t1["refresh_token"]})
    assert t2.status_code == 200 and t2.json()["refresh_token"] != t1["refresh_token"]
    # reutilizar el token viejo => rechazo y toda la familia queda revocada
    reuse = w.c.post("/api/v1/auth/refresh", json={"refresh_token": t1["refresh_token"]})
    assert reuse.status_code == 401
    after = w.c.post("/api/v1/auth/refresh", json={"refresh_token": t2.json()["refresh_token"]})
    assert after.status_code == 401


def test_logout_revokes_refresh(w):
    w.staff("ADMIN", "admin@x.pe")
    t = w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": PW}).json()
    assert w.c.post("/api/v1/auth/logout", json={"refresh_token": t["refresh_token"]}).status_code == 204
    assert w.c.post("/api/v1/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401


def test_deactivated_user_loses_access_immediately(w, db):
    w.staff("ADMIN", "admin@x.pe")
    h = w.login("admin@x.pe")
    db.query(User).update({"is_active": False})
    db.commit()
    assert w.c.get("/api/v1/auth/me", headers=h).status_code == 401


def test_student_login_with_code_and_pin(w):
    school = w.school()
    w.staff("TEACHER", "t@x.pe", school)
    th = w.login("t@x.pe")
    room = w.classroom(th)
    st = w.student(th, room, 1)
    r = w.c.post("/api/v1/auth/student-login", json={"login_code": st["login_code"].lower(), "pin": st["pin"],
                                                     "device_id": new_device()})
    assert r.status_code == 200 and r.json()["user"]["role"] == "STUDENT"
    bad = w.c.post("/api/v1/auth/student-login", json={"login_code": st["login_code"], "pin": "000000",
                                                       "device_id": new_device()})
    assert bad.status_code == 401
    # un estudiante no puede entrar por el login de docentes
    assert w.c.post("/api/v1/auth/login", json={"email": "x@x.pe", "password": st["pin"]}).status_code == 401


def test_extra_fields_rejected_mass_assignment(w):
    w.staff("ADMIN", "admin@x.pe")
    r = w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": PW, "role": "ADMIN"})
    assert r.status_code == 422


def test_no_secrets_in_logs(w, caplog):
    w.staff("ADMIN", "admin@x.pe")
    with caplog.at_level("DEBUG"):
        r = w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": PW})
    assert PW not in caplog.text and r.json()["access_token"] not in caplog.text
    _ = timedelta
