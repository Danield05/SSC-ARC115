"""Reglas de negocio del módulo devices."""

import secrets
from datetime import UTC, datetime

from app.core.security import hash_api_key
from app.modules.devices import repository

ID_PREFIX = "ESP32-GP03-"
MAX_ID_ATTEMPTS = 20


class DeviceNotFoundError(Exception):
    pass


def to_public(device: dict) -> dict:
    return {
        "device_id": device["device_id"],
        "name": device.get("name", ""),
        "promoter_email": device.get("promoter_email", ""),
        "active": device.get("active", True),
        "created_at": device.get("created_at", ""),
    }


def _new_api_key() -> str:
    return secrets.token_urlsafe(32)


def create_device(name: str, promoter_email: str) -> tuple[dict, str]:
    """Devuelve (dispositivo, clave en claro). La clave solo existe en esta respuesta.

    El identificador lo asigna el sistema (ESP32-GP03-01, -02…). Si el número ya está tomado
    (por ejemplo, un dispositivo creado a mano antes), se pasa al siguiente.
    """
    api_key = _new_api_key()
    for _ in range(MAX_ID_ATTEMPTS):
        item = {
            "device_id": f"{ID_PREFIX}{repository.next_id_number():02d}",
            "name": name,
            "promoter_email": promoter_email,
            "api_key_hash": hash_api_key(api_key),
            "active": True,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
        if repository.create_device(item):
            return to_public(item), api_key
    raise RuntimeError("No se pudo asignar un identificador de dispositivo")


def list_devices(role: str, email: str) -> list[dict]:
    """Admin y evaluador ven todos; el promotor solo los suyos."""
    devices = repository.list_devices()
    if role == "promoter":
        devices = [d for d in devices if d.get("promoter_email") == email]
    return sorted((to_public(d) for d in devices), key=lambda d: d["device_id"])


def update_device(device_id: str, changes: dict) -> dict:
    changes = {k: v for k, v in changes.items() if v is not None}
    if not changes:
        device = repository.get_device(device_id)
    else:
        device = repository.update_device(device_id, changes)
    if device is None:
        raise DeviceNotFoundError(device_id)
    return to_public(device)


def rotate_api_key(device_id: str) -> str:
    api_key = _new_api_key()
    if repository.update_device(device_id, {"api_key_hash": hash_api_key(api_key)}) is None:
        raise DeviceNotFoundError(device_id)
    return api_key
