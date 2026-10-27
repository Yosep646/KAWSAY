#!/usr/bin/env python3
"""Utilidad de desarrollo multiplataforma (Windows / macOS / Linux). Solo usa la biblioteca estándar.

  python scripts/dev.py setup     crea .venv, instala dependencias, genera backend/.env con secretos aleatorios y migra la base SQLite
  python scripts/dev.py admin     crea el primer administrador (pide correo, nombre y contraseña)
  python scripts/dev.py run       arranca el backend en http://127.0.0.1:8000  (documentación en /docs)
  python scripts/dev.py web       instala y arranca el panel docente en http://localhost:5173
  python scripts/dev.py demo      arranca el backend y carga datos DEMO completos (aula multigrado, alertas, etc.)
  python scripts/dev.py test      ejecuta todas las pruebas (backend, ML y panel)
  python scripts/dev.py backup    copia consistente de la base de datos
"""
import getpass
import os
import secrets
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND, WEB, VENV = ROOT / "backend", ROOT / "teacher-web", ROOT / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
DEMO_ADMIN = ("admin@demo.pe", "Kawsay-Demo-Local-2026")
DEMO_TEACHER = ("maestra@demo.pe", "Aula-Multigrado-2026!")


def run(cmd: list, cwd: Path = ROOT, env: dict | None = None, check: bool = True) -> int:
    print("»", " ".join(str(c) for c in cmd))
    return subprocess.run([str(c) for c in cmd], cwd=cwd, env={**os.environ, **(env or {})}, check=check).returncode


def ensure_python() -> None:
    if sys.version_info < (3, 10):
        sys.exit("Se requiere Python 3.10 o superior (recomendado 3.12).")


def setup(with_ml: bool = True) -> None:
    ensure_python()
    if not PY.exists():
        run([sys.executable, "-m", "venv", VENV])
    run([PY, "-m", "pip", "install", "--upgrade", "pip", "-q"])
    run([PY, "-m", "pip", "install", "-r", BACKEND / "requirements-dev.txt", "-q"])
    if with_ml:
        run([PY, "-m", "pip", "install", "-r", ROOT / "ml" / "requirements.txt", "-q"])
    env_file = BACKEND / ".env"
    if not env_file.exists():
        env_file.write_text(f"APP_ENV=development\nDATABASE_URL=sqlite:///./data/kawsay.db\nJWT_SECRET={secrets.token_hex(32)}\n"
                            "CORS_ORIGINS=http://localhost:5173\nAI_PROVIDER=disabled\n", encoding="utf-8")
        try:
            os.chmod(env_file, 0o600)
        except OSError:
            pass
        print("» backend/.env creado con un JWT_SECRET aleatorio (no lo subas a Git)")
    run([PY, "-m", "alembic", "upgrade", "head"], cwd=BACKEND)
    print("\nListo. Siguiente: `python scripts/dev.py demo` (con datos de ejemplo) o `python scripts/dev.py admin` + `run`.")


def wait_ready(url: str = "http://127.0.0.1:8000/ready", seconds: int = 60) -> None:
    for _ in range(seconds):
        try:
            if urllib.request.urlopen(url, timeout=2).status == 200:
                return
        except Exception:
            time.sleep(1)
    sys.exit("El backend no respondió a tiempo.")


def create_admin(email: str | None = None, password: str | None = None, name: str = "Administrador") -> None:
    email = email or input("Correo del administrador: ").strip()
    name = name if password else (input("Nombre: ").strip() or name)
    password = password or getpass.getpass("Contraseña (mínimo 12 caracteres, no común): ")
    run([PY, "-m", "app.cli", "create-admin", email, name], cwd=BACKEND, env={"ADMIN_PASSWORD": password}, check=False)


def start_backend(reload: bool = True) -> subprocess.Popen:
    cmd = [str(PY), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"] + (["--reload"] if reload else [])
    print("»", " ".join(cmd))
    return subprocess.Popen(cmd, cwd=BACKEND)


def demo() -> None:
    if not PY.exists() or not (BACKEND / ".env").exists():
        setup()
    create_admin(*DEMO_ADMIN, name="Admin Demo")
    proc = start_backend(reload=False)
    try:
        wait_ready()
        run([PY, ROOT / "scripts" / "demo_e2e.py"], env={
            "KAWSAY_URL": "http://127.0.0.1:8000", "KAWSAY_ADMIN_EMAIL": DEMO_ADMIN[0], "KAWSAY_ADMIN_PASSWORD": DEMO_ADMIN[1],
            "KAWSAY_TEACHER_EMAIL": DEMO_TEACHER[0], "KAWSAY_TEACHER_PASSWORD": DEMO_TEACHER[1]})
        print(f"""
================ DATOS DEMO CARGADOS ================
 Backend + documentación:  http://127.0.0.1:8000/docs
 Panel docente (otra terminal: python scripts/dev.py web) → http://localhost:5173
   Docente:        {DEMO_TEACHER[0]}   /   {DEMO_TEACHER[1]}
   Administrador:  {DEMO_ADMIN[0]}   /   {DEMO_ADMIN[1]}
 (Credenciales SOLO de demostración local: cámbialas o borra backend/data/kawsay.db antes de un uso real.)
 El servidor sigue corriendo; Ctrl+C para detenerlo.
=====================================================""")
        proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        proc.terminate()


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "setup":
        setup(with_ml="--no-ml" not in sys.argv)
    elif cmd == "admin":
        create_admin()
    elif cmd == "run":
        if not PY.exists():
            setup()
        try:
            start_backend().wait()
        except KeyboardInterrupt:
            pass
    elif cmd == "web":
        npm = "npm.cmd" if os.name == "nt" else "npm"
        run([npm, "install"], cwd=WEB)
        run([npm, "run", "dev"], cwd=WEB)
    elif cmd == "demo":
        demo()
    elif cmd == "test":
        run([PY, "-m", "pytest", "-q"], cwd=BACKEND)
        run([PY, "-m", "pytest", "ml/tests", "-q"], cwd=ROOT)
        npm = "npm.cmd" if os.name == "nt" else "npm"
        run([npm, "install"], cwd=WEB)
        run([npm, "test"], cwd=WEB)
    elif cmd == "backup":
        run([PY, "-m", "app.cli", "backup", ROOT / "backups"], cwd=BACKEND)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
