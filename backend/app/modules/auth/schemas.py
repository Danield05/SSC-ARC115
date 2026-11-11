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
    """El administrador solo indica correo, nombre y rol: la contraseña la genera el sistema."""

    email: Email
    name: str = Field(default="", max_length=80)
    role: Role


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    active: bool | None = None
    role: Role | None = None


class ForgotPasswordRequest(BaseModel):
    email: Email


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class MessageOut(BaseModel):
    message: str


class UserOut(BaseModel):
    email: str
    name: str = ""
    role: Role
    active: bool
    created_at: str
    must_change_password: bool = False


TokenResponse.model_rebuild()
