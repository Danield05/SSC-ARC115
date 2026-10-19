"""Reglas de negocio del módulo auth: usuarios, contraseñas y sesiones."""

from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth import repository


class UserExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class SelfDeactivationError(Exception):
    pass


class AuthNotConfiguredError(Exception):
    pass


def to_public(user: dict) -> dict:
    return {
        "email": user["email"],
        "role": user["role"],
        "active": user.get("active", True),
        "created_at": user.get("created_at", ""),
    }


def authenticate(email: str, password: str) -> tuple[str, dict] | None:
    """Devuelve (token, usuario público) o None si las credenciales no son válidas."""
    secret = get_settings().jwt_secret
    if not secret:
        raise AuthNotConfiguredError("JWT_SECRET no está configurado")
    user = repository.get_user(email)
    if user is None or not user.get("active", True):
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return create_access_token(user["email"], user["role"], secret), to_public(user)


def create_user(email: str, password: str, role: str) -> dict:
    item = {
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "active": True,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    if not repository.create_user(item):
        raise UserExistsError(email)
    return to_public(item)


def list_users() -> list[dict]:
    return sorted((to_public(u) for u in repository.list_users()), key=lambda u: u["email"])


def set_user_active(email: str, active: bool, acting_email: str) -> dict:
    if email == acting_email and not active:
        raise SelfDeactivationError(email)
    user = repository.set_active(email, active)
    if user is None:
        raise UserNotFoundError(email)
    return to_public(user)
