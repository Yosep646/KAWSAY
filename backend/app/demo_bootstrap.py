"""Opt-in DEMO staff; passwords are provided only through server secrets."""
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_engine
from app.modules.schools.models import School
from app.modules.users.models import Role, User
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_staff_user


def bootstrap():
    if os.environ.get("KAWSAY_DEMO_BOOTSTRAP") != "1":
        return
    credentials = {role: (os.environ[f"KAWSAY_DEMO_{role}_EMAIL"], os.environ[f"KAWSAY_DEMO_{role}_PASSWORD"])
                   for role in ("ADMIN", "TEACHER")}
    with Session(get_engine(), expire_on_commit=False) as db:
        school = db.scalar(select(School).where(School.code == "OFFLINE-DEMO-20261030", School.deleted_at.is_(None)))
        if school is None:
            school = School(name="Escuela ficticia KAWSAY offline", code="OFFLINE-DEMO-20261030", region="DEMO")
            db.add(school)
            db.flush()
        for role, (email, password) in credentials.items():
            existing = db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
            if existing is not None:
                if existing.role != role:
                    raise RuntimeError("A DEMO email already belongs to a different role")
                continue
            create_staff_user(db, UserCreate(role=role, email=email, password=password,
                display_name="Administrador DEMO" if role == Role.ADMIN else "Docente DEMO",
                school_id=school.id if role == Role.TEACHER else None))
        db.commit()
    print("KAWSAY: DEMO initialization completed without personal student data", flush=True)


if __name__ == "__main__":
    bootstrap()
