"""SQLite con varios usuarios a la vez: sin 'database is locked', sin duplicados, sin bloqueos por llamadas lentas."""
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.core.database import get_engine
from app.modules.learning.models import LearningAttempt
from tests.conftest import PW
from tests.fakes import FakeProvider, good, install
from tests.test_ai_gateway import _ai_assignment
from tests.test_sync_reto10 import _ev, _login, _published, _pull


def test_many_concurrent_logins_and_writes_never_fail_with_locked_database(w):
    school = w.school()
    for i in range(6):
        w.staff("TEACHER", f"t{i}@x.pe", school)
    app = w.app

    def work(i: int) -> list[int]:
        c = TestClient(app, raise_server_exceptions=False)
        codes = []
        for _ in range(4):
            r = c.post("/api/v1/auth/login", json={"email": f"t{i % 6}@x.pe", "password": PW})
            codes.append(r.status_code)
            if r.status_code == 200:
                h = {"Authorization": f"Bearer {r.json()['access_token']}"}
                codes.append(c.post("/api/v1/classrooms", headers=h, json={"name": f"Aula {i}-{uuid.uuid4().hex[:6]}", "academic_year": 2026}).status_code)
                codes.append(c.get("/api/v1/classrooms", headers=h).status_code)
        return codes

    with ThreadPoolExecutor(max_workers=12) as ex:
        results = [c for r in ex.map(work, range(24)) for c in r]
    assert set(results) <= {200, 201}, sorted(set(results))      # ni 500 ni "database is locked"


def test_concurrent_refresh_with_same_token_yields_one_winner_and_no_server_errors(w):
    w.staff("ADMIN", "admin@x.pe")
    t = w.c.post("/api/v1/auth/login", json={"email": "admin@x.pe", "password": PW}).json()
    app = w.app

    def go(_):
        return TestClient(app, raise_server_exceptions=False).post("/api/v1/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code

    with ThreadPoolExecutor(max_workers=8) as ex:
        codes = list(ex.map(go, range(8)))
    assert 500 not in codes and codes.count(200) == 1 and set(codes) <= {200, 401}


def test_concurrent_pushes_of_the_same_events_do_not_duplicate_attempts(w, db):
    _, _, _, (st,) = _published(w)
    sh = _login(w, st)
    t = _pull(w, sh)["tasks"][0]
    events = [_ev(t["student_assignment_id"], t["questions"][i]["id"], 1, True, minutes=i) for i in range(5)]
    app = w.app

    def push(_):
        c = TestClient(app, raise_server_exceptions=False)
        r = c.post("/api/v1/sync/push", headers=sh, json={"device_id": "66666666-6666-6666-6666-666666666666", "events": events})
        return r.status_code, sorted({x["status"] for x in r.json()["results"]}) if r.status_code == 200 else None

    with ThreadPoolExecutor(max_workers=6) as ex:
        out = list(ex.map(push, range(6)))
    assert all(code == 200 for code, _ in out), out
    assert db.query(LearningAttempt).count() == 5                 # 6 envíos simultáneos del mismo lote => 5 intentos


def test_slow_ai_call_does_not_block_other_users(w):
    ta, _, _, a = _ai_assignment(w, grades=(1,))

    def slow(req):
        time.sleep(1.5)
        return good(req)

    install(w.app, FakeProvider(slow))
    app = w.app

    def adapt():
        return TestClient(app).post(f"/api/v1/assignments/{a['id']}/adapt", headers=ta, json={}).status_code

    with ThreadPoolExecutor(max_workers=2) as ex:
        fut = ex.submit(adapt)
        time.sleep(0.4)
        t0 = time.monotonic()
        r = TestClient(app).get("/api/v1/auth/me", headers=ta)
        elapsed = time.monotonic() - t0
        assert fut.result() == 200
    assert r.status_code == 200 and elapsed < 1.0, f"otra petición esperó {elapsed:.2f}s mientras la IA respondía"
    _ = get_engine
