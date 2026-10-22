"""Reglas de negocio del módulo auth: usuarios, contraseñas y sesiones."""

import logging
import secrets
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth import repository
from app.modules.notifications import service as notifications
from app.modules.notifications.service import MailError

logger = logging.getLogger(__name__)

ROLE_LABELS = {
    "admin": "Administrador",
    "promoter": "Promotor de salud",
    "viewer": "Evaluador (solo lectura)",
}

RESET_MINUTES = 30
RESET_COOLDOWN_SECONDS = 60
# Sin caracteres que se confunden al leer o copiar (0/O, 1/l/I).
_PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"  # noqa: S105


class UserExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class SelfChangeError(Exception):
    """El administrador intentó desactivarse o cambiarse el rol a sí mismo."""


class AuthNotConfiguredError(Exception):
    pass


class InvalidPasswordError(Exception):
    pass


class SamePasswordError(Exception):
    pass


class NotPendingError(Exception):
    """Se pidió reenviar la invitación a quien ya activó su cuenta."""


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds").replace("+00:00", "Z")


def generate_temp_password(length: int = 12) -> str:
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))


def to_public(user: dict) -> dict:
    return {
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user["role"],
        "active": user.get("active", True),
        "created_at": user.get("created_at", ""),
        "must_change_password": user.get("must_change_password", False),
    }


def get_public(email: str) -> dict:
    user = repository.get_user(email)
    if user is None:
        raise UserNotFoundError(email)
    return to_public(user)


def _match_password(user: dict, password: str) -> str | None:
    """'main' si es la contraseña de siempre, 'reset' si es la provisional de recuperación."""
    if verify_password(password, user["password_hash"]):
        return "main"
    reset_hash = user.get("reset_hash")
    if reset_hash and user.get("reset_expires", "") > _iso(_now()):
        if verify_password(password, reset_hash):
            return "reset"
    return None


def authenticate(email: str, password: str) -> tuple[str, dict] | None:
    """Devuelve (token, usuario público) o None si las credenciales no son válidas."""
    secret = get_settings().jwt_secret
    if not secret:
        raise AuthNotConfiguredError("JWT_SECRET no está configurado")
    user = repository.get_user(email)
    if user is None or not user.get("active", True):
        return None
    matched = _match_password(user, password)
    if matched is None:
        return None
    if matched == "reset" and not user.get("must_change_password"):
        # Entró con la provisional: debe crear una contraseña nueva antes de usar el sistema.
        user = repository.update_user(email, {"must_change_password": True}) or user
    return create_access_token(user["email"], user["role"], secret), to_public(user)


def create_user(
    email: str, password: str, role: str, name: str = "", must_change_password: bool = False
) -> dict:
    item = {
        "email": email,
        "name": name.strip(),
        "password_hash": hash_password(password),
        "role": role,
        "active": True,
        "must_change_password": must_change_password,
        "created_at": _iso(_now()),
    }
    if not item["name"]:
        del item["name"]
    if not repository.create_user(item):
        raise UserExistsError(email)
    return to_public(item)


def invite_user(email: str, role: str, name: str) -> dict:
    """Crea al usuario con una contraseña provisional y se la envía por correo."""
    temp = generate_temp_password()
    user = create_user(email, temp, role, name, must_change_password=True)
    try:
        notifications.send_invitation(email, name, ROLE_LABELS[role], temp)
    except MailError:
        repository.delete_user(email)  # Sin correo no hay forma de entregar la contraseña.
        raise
    return user


def resend_invite(email: str) -> dict:
    user = repository.get_user(email)
    if user is None:
        raise UserNotFoundError(email)
    if not user.get("must_change_password"):
        raise NotPendingError(email)
    temp = generate_temp_password()
    updated = repository.update_user(email, {"password_hash": hash_password(temp)})
    if updated is None:
        raise UserNotFoundError(email)
    role_label = ROLE_LABELS[updated["role"]]
    notifications.send_invitation(email, updated.get("name", ""), role_label, temp)
    return to_public(updated)


def list_users() -> list[dict]:
    return sorted((to_public(u) for u in repository.list_users()), key=lambda u: u["email"])


def update_user(email: str, active: bool | None, role: str | None, acting_email: str) -> dict:
    if email == acting_email and (active is False or role is not None):
        raise SelfChangeError(email)
    changes = {}
    if active is not None:
        changes["active"] = active
    if role is not None:
        changes["role"] = role
    user = repository.update_user(email, changes) if changes else repository.get_user(email)
    if user is None:
        raise UserNotFoundError(email)
    return to_public(user)


def request_password_reset(email: str) -> None:
    """Envía una contraseña provisional. Nunca revela si el correo existe.

    La contraseña de siempre sigue valiendo hasta que se use la provisional, así que pedir un
    reinicio ajeno no bloquea a nadie. Un enfriamiento evita el correo masivo a un tercero.
    """
    user = repository.get_user(email)
    if user is None or not user.get("active", True):
        return
    last = user.get("reset_requested_at", "")
    if last and last > _iso(_now() - timedelta(seconds=RESET_COOLDOWN_SECONDS)):
        return
    temp = generate_temp_password()
    now = _now()
    repository.update_user(
        email,
        {
            "reset_hash": hash_password(temp),
            "reset_expires": _iso(now + timedelta(minutes=RESET_MINUTES)),
            "reset_requested_at": _iso(now),
        },
    )
    try:
        notifications.send_password_reset(email, user.get("name", ""), temp, RESET_MINUTES)
    except MailError:
        logger.error("No se pudo enviar la contraseña provisional a un usuario")


def change_password(email: str, current_password: str, new_password: str) -> dict:
    user = repository.get_user(email)
    if user is None:
        raise UserNotFoundError(email)
    if _match_password(user, current_password) is None:
        raise InvalidPasswordError(email)
    if new_password == current_password:
        raise SamePasswordError(email)
    updated = repository.update_user(
        email,
        {"password_hash": hash_password(new_password), "must_change_password": False},
        remove=("reset_hash", "reset_expires", "reset_requested_at"),
    )
    if updated is None:
        raise UserNotFoundError(email)
    return to_public(updated)
