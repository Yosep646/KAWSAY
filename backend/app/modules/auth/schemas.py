import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PasswordLogin(_In):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    device_id: uuid.UUID | None = None


class StudentLogin(_In):
    login_code: str = Field(min_length=4, max_length=12)
    pin: str = Field(min_length=4, max_length=12)
    device_id: uuid.UUID


class RefreshIn(_In):
    refresh_token: str = Field(min_length=20, max_length=200)


class UserBrief(BaseModel):
    id: uuid.UUID
    role: str
    display_name: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int
    user: UserBrief


class ChangePasswordIn(_In):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=128)
