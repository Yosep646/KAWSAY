"""Servidores E2E: SQLite temporal + backend real + datos DEMO + Vite.

Lo inicia npm run test:e2e; nunca usa backend/data/kawsay.db.
"""
import os
import secrets
import socket
import subprocess
import sys
import sysconfig
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
WEB = ROOT / "teacher-web"
API_URL = "http://127.0.0.1:18000"
WEB_URL = "http://127.0.0.1:15173"


@contextmanager
def temporary_database() -> Iterator[str]:
    folder = tempfile.TemporaryDirectory(prefix=".kawsay-e2e-", dir=ROOT)
    try:
        yield folder.name
    finally:
        # Windows puede liberar los handles de SQLite después de terminar el árbol.
        # Reintentar el borrado, sin ocultar un bloqueo persistente.
        for attempt in range(20):
            try:
                folder.cleanup()
                break
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.25)


def run(args: list[str], cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(args, cwd=cwd, env=env, check=True)


def stop(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def main() -> None:
    # Fallar antes de crear datos si los puertos pertenecen a otra instancia.
    for port in (18000, 15173):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))

    with temporary_database() as folder:
        env = {
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "APP_ENV": "test",
            "LOG_LEVEL": "WARNING",
            "DATABASE_URL": f"sqlite:///{Path(folder).as_posix()}/browser.db",
            "JWT_SECRET": secrets.token_hex(32),
            "CORS_ORIGINS": WEB_URL,
            "AI_PROVIDER": "disabled",
            "AI_API_KEY": "",
            "AUTOMATION_WEBHOOK_URL": "",
            "AUTOMATION_WEBHOOK_SECRET": "",
            "ML_ALLOW_EXPERIMENTAL": "false",
            "KAWSAY_URL": API_URL,
            "KAWSAY_ADMIN_EMAIL": "admin@demo.pe",
            "KAWSAY_ADMIN_PASSWORD": "Kawsay-Demo-Local-2026",
            "KAWSAY_TEACHER_EMAIL": "maestra@demo.pe",
            "KAWSAY_TEACHER_PASSWORD": "Aula-Multigrado-2026!",
            "ADMIN_PASSWORD": "Kawsay-Demo-Local-2026",
            "VITE_API_URL": API_URL,
            "VITE_TEST_TEACHER_EMAIL": "maestra@demo.pe",
            "VITE_TEST_TEACHER_PASSWORD": "Aula-Multigrado-2026!",
            "LOGIN_RATE_LIMIT_PER_MINUTE": "100",
            "KAWSAY_E2E_DB": str(Path(folder) / "browser.db"),
            "KAWSAY_E2E_PYTHON": sys.executable,
        }
        run([sys.executable, "-m", "alembic", "upgrade", "head"], BACKEND, env)
        run([sys.executable, "-m", "app.cli", "create-admin", env["KAWSAY_ADMIN_EMAIL"], "Admin DEMO"], BACKEND, env)
        # Launch the interpreter directly, avoiding Windows' venv redirector and
        # an orphaned uvicorn child when process-tree inspection is unavailable.
        backend_env = {**env, "PYTHONPATH": os.pathsep.join([sysconfig.get_path("purelib"), str(ROOT)])}
        backend = subprocess.Popen(
            [getattr(sys, "_base_executable", sys.executable), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18000",
             "--no-access-log"],
            cwd=BACKEND, env=backend_env,
        )
        web = None
        try:
            for _ in range(120):
                if backend.poll() is not None:
                    raise RuntimeError("El backend E2E terminó antes de estar listo")
                try:
                    with urllib.request.urlopen(f"{API_URL}/ready", timeout=2) as response:
                        if response.status == 200:
                            break
                except (urllib.error.URLError, TimeoutError):
                    pass
                time.sleep(0.5)
            else:
                raise RuntimeError("El backend E2E no respondió a tiempo")
            run([sys.executable, str(ROOT / "scripts" / "demo_e2e.py")], ROOT, env)
            run(["node", str(WEB / "node_modules" / "vitest" / "vitest.mjs"),
                 "run", "src/test/integration.test.ts"], WEB, env)
            production = any("playwright.offline.config" in arg for arg in sys.argv)
            vite = ["node", str(WEB / "node_modules" / "vite" / "bin" / "vite.js")]
            if production:
                run([*vite, "build"], WEB, env)
            web = subprocess.Popen(
                [*vite, *(["preview"] if production else []),
                 "--host", "127.0.0.1", "--port", "15173", "--strictPort"],
                cwd=WEB, env=env,
            )
            for _ in range(120):
                if web.poll() is not None or backend.poll() is not None:
                    raise RuntimeError("Un servidor E2E se detuvo antes de estar listo")
                try:
                    with urllib.request.urlopen(WEB_URL, timeout=2) as response:
                        if response.status == 200:
                            break
                except (urllib.error.URLError, TimeoutError):
                    pass
                time.sleep(0.5)
            else:
                raise RuntimeError("El panel E2E no respondió a tiempo")
            run(["node", str(WEB / "node_modules" / "@playwright" / "test" / "cli.js"),
                 "test", *sys.argv[1:]], WEB, env)
        finally:
            if web is not None:
                stop(web)
            stop(backend)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
