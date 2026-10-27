import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_roles
from app.modules.users import service
from app.modules.users.models import Role, User
from app.modules.users.schemas import UserCreate, UserOut, UserPatch

router = APIRouter(prefix="/users", tags=["users"])
DB = Annotated[Session, Depends(get_db)]
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]


@router.post("", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: DB, _: Admin) -> User:
    return service.create_staff_user(db, body)


@router.get("", response_model=list[UserOut])
def list_users(db: DB, _: Admin, limit: Annotated[int, Query(ge=1, le=100)] = 50,
               offset: Annotated[int, Query(ge=0)] = 0) -> list[User]:
    return service.list_users(db, limit, offset)


@router.patch("/{user_id}", response_model=UserOut)
def patch_user(user_id: uuid.UUID, body: UserPatch, db: DB, admin: Admin) -> User:
    return service.set_active(db, admin, user_id, body.is_active)
