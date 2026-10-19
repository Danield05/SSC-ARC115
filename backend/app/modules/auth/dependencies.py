"""Dependencias de FastAPI: usuario autenticado y control por rol."""

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.modules.auth import repository

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    email: str
    role: str


def _unauthorized(detail: str = "No autenticado") -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008
) -> CurrentUser:
    secret = get_settings().jwt_secret
    if creds is None or not secret:
        raise _unauthorized()
    try:
        payload = decode_access_token(creds.credentials, secret)
    except jwt.PyJWTError:
        raise _unauthorized("Sesión inválida o vencida") from None
    # El rol y el estado se leen de la base: un cambio de rol o una baja aplican de inmediato.
    user = repository.get_user(payload.get("sub", ""))
    if user is None or not user.get("active", True):
        raise _unauthorized("Usuario inactivo o inexistente")
    return CurrentUser(email=user["email"], role=user["role"])


def require_roles(*roles: str):
    def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:  # noqa: B008
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permiso para esta acción")
        return user

    return checker
