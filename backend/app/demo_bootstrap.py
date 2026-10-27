"""Inicialización opt-in de una cuenta docente con datos exclusivamente ficticios.

Sólo se ejecuta con KAWSAY_DEMO_BOOTSTRAP=1 y credenciales en variables privadas
de entorno. No hay contraseñas por defecto ni puntos de acceso públicos para crear usuarios.
"""
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.modules.schools.models import School
from app.modules.users.models import Role, User
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_staff_user

DEMO_SCHOOL_CODE = "KAWSAY-DEMO-2026"


def bootstrap_teacher() -> None:
    if os.environ.get("KAWSAY_DEMO_BOOTSTRAP") != "1":
        return
    email = os.environ.get("KAWSAY_DEMO_TEACHER_EMAIL", "").strip().lower()
    password = os.environ.get("KAWSAY_DEMO_TEACHER_PASSWORD", "")
    if not email or not password:
        raise RuntimeError("La inicializacion DEMO requiere correo y clave definidos en Render")

    # Nunca imprimir ni registrar la contraseña, ni almacenarla en archivos.
    with Session(get_engine(), expire_on_commit=False) as db:
        existing = db.scalar(select(User).where(User.email == email, User.deleted_at.is_(None)))
        if existing is not None:
            if existing.role != Role.TEACHER:
                raise RuntimeError("El correo DEMO ya pertenece a otro rol")
            print("KAWSAY DEMO: cuenta docente existente (sin modificar)", flush=True)
            return

        school = db.scalar(select(School).where(
            School.code == DEMO_SCHOOL_CODE, School.deleted_at.is_(None)))
        if school is None:
            school = School(name="Institucion educativa KAWSAY - DEMO", code=DEMO_SCHOOL_CODE,
                            region="Datos ficticios")
            db.add(school)
            db.flush()
        data = UserCreate(role="TEACHER", email=email, password=password,
                          display_name="Docente demostracion", school_id=school.id)
        create_staff_user(db, data)
        print("KAWSAY DEMO: docente habilitado con datos ficticios", flush=True)


def bootstrap_administrator() -> None:
    if os.getenv("KAWSAY_DEMO_ADMIN_ENABLED") != "1":
        return
    username = os.environ["KAWSAY_DEMO_ADMIN_EMAIL"].strip().lower()
    passphrase = os.environ["KAWSAY_DEMO_ADMIN_PASSWORD"]
    with Session(get_engine(), expire_on_commit=False) as db:
        existing = db.scalar(select(User).where(User.email == username, User.deleted_at.is_(None)))
        if existing is not None:
            if existing.role != Role.ADMIN:
                raise ValueError("El correo ya pertenece a otro rol")
            print("KAWSAY DEMO: administrador existente", flush=True)
            return
        create_staff_user(db, UserCreate(
            role="ADMIN", email=username, password=passphrase, display_name="Administrador KAWSAY"
        ))
        print("KAWSAY DEMO: administrador creado", flush=True)


if __name__ == "__main__":
    bootstrap_teacher()
    bootstrap_administrator()
