import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["TEACHER", "ADMIN"]
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    school_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _teacher_needs_school(self) -> "UserCreate":
        if self.role == "TEACHER" and self.school_id is None:
            raise ValueError("school_id es obligatorio para docentes")
        return self


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str | None
    role: str
    display_name: str
    is_active: bool
    created_at: datetime


class UserPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool
