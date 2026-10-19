"""Modelos de datos del módulo auth."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

Role = Literal["admin", "promoter", "viewer"]

Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    user: "UserOut"


class UserCreate(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=128)
    role: Role


class UserUpdate(BaseModel):
    active: bool


class UserOut(BaseModel):
    email: str
    role: Role
    active: bool
    created_at: str


TokenResponse.model_rebuild()
