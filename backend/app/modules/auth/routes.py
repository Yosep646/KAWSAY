from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_roles
from app.core.rate_limit import login_rate_limit
from app.modules.auth import service
from app.modules.auth.schemas import ChangePasswordIn, PasswordLogin, RefreshIn, StudentLogin, StudentEmailLoginIn, TokenOut, UserBrief
from app.modules.users.models import Role, User

router = APIRouter(prefix="/auth", tags=["auth"])
DB = Annotated[Session, Depends(get_db)]


@router.post("/login", response_model=TokenOut, dependencies=[Depends(login_rate_limit)])
def login(body: PasswordLogin, db: DB) -> dict:
    return service.login_with_password(db, body.email, body.password, body.device_id)


@router.post("/student-login", response_model=TokenOut, dependencies=[Depends(login_rate_limit)])
def student_login(body: StudentLogin, db: DB) -> dict:
    return service.login_student(db, body.login_code, body.pin, body.device_id)


@router.post("/student-email-login", response_model=TokenOut, dependencies=[Depends(login_rate_limit)])
def student_email_login(body: StudentEmailLoginIn, db: DB) -> dict:
    return service.login_student_email(db, str(body.email), body.password, body.device_id)


@router.post("/refresh", response_model=TokenOut, dependencies=[Depends(login_rate_limit)])
def refresh(body: RefreshIn, db: DB) -> dict:
    return service.refresh(db, body.refresh_token)


@router.post("/logout", status_code=204)
def logout(body: RefreshIn, db: DB) -> Response:
    service.logout(db, body.refresh_token)
    return Response(status_code=204)


@router.get("/me", response_model=UserBrief)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.post("/change-password", response_model=TokenOut, dependencies=[Depends(login_rate_limit)])
def change_password(body: ChangePasswordIn, db: DB,
                    user: Annotated[User, Depends(require_roles(Role.TEACHER, Role.ADMIN))]) -> dict:
    return service.change_password(db, user, body.current_password, body.new_password)
