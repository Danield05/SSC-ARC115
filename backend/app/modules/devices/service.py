"""Reglas de negocio del módulo devices."""

import secrets
from datetime import UTC, datetime, timedelta

from app.core.security import hash_api_key, verify_api_key
from app.modules.devices import repository
from app.modules.patients import service as patients_service

ID_PREFIX = "ESP32-GP03-"
MAX_ID_ATTEMPTS = 20


class DeviceNotFoundError(Exception):
    pass


class InvalidDeviceKeyError(Exception):
    """Clave ausente o inválida, dispositivo desconocido o dado de baja."""


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


def authenticate_device(device_id: str, api_key: str | None) -> dict:
    """Valida la `x-api-key` contra el hash guardado. Devuelve el dispositivo."""
    device = repository.get_device(device_id)
    if (
        not api_key
        or device is None
        or not device.get("active", True)
        or not verify_api_key(api_key, device.get("api_key_hash", ""))
    ):
        raise InvalidDeviceKeyError(device_id)
    return device


# --- Órdenes «Medir a este paciente» -------------------------------------------------------
# La web crea la orden; el ESP32 la consulta con su clave (un API HTTP no puede llamarlo, está
# detrás del router) y mide. Una sola orden vigente por dispositivo, guardada en su ítem.
PENDING_TTL = timedelta(minutes=2)  # cuánto espera la orden a que el aparato la tome
MEASURING_TTL = timedelta(minutes=5)  # cuánto tiene el aparato para medir una vez que la tomó
OPEN_STATUSES = ("pendiente", "tomada")


class CommandBusyError(Exception):
    """El aparato ya está midiendo a otro paciente."""


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _effective_status(command: dict, now: datetime) -> str:
    """El estado guardado, salvo que ya se haya vencido su plazo (se calcula al leer)."""
    status = command["status"]
    if status == "pendiente" and now > _parse(command["expires_at"]):
        return "expirada"
    if status == "tomada" and now > _parse(command["taken_at"]) + MEASURING_TTL:
        return "expirada"
    return status


def _command_public(command: dict, now: datetime) -> dict:
    return {
        "command_id": command["command_id"],
        "patient_code": command["patient_code"],
        "status": _effective_status(command, now),
        "created_at": command["created_at"],
        "expires_at": command["expires_at"],
        "taken_at": command.get("taken_at"),
        "completed_at": command.get("completed_at"),
        "ts": command.get("ts"),
    }


def _device_for(device_id: str, role: str, email: str) -> dict:
    """El dispositivo, si el rol lo ve (el promotor, solo los suyos)."""
    device = repository.get_device(device_id)
    if device is None or (role == "promoter" and device.get("promoter_email") != email):
        raise DeviceNotFoundError(device_id)
    return device


def create_measure_order(device_id: str, patient_code: str, role: str, email: str) -> dict:
    """Crea la orden de medir a `patient_code`. Lanza PatientNotFoundError si el rol no ve al
    paciente, y CommandBusyError si el aparato ya tiene una orden en curso."""
    device = _device_for(device_id, role, email)
    if not device.get("active", True):
        raise DeviceNotFoundError(device_id)
    patients_service.get_patient(patient_code, role, email)
    now = _now()
    current = device.get("command")
    if current and _effective_status(current, now) == "tomada":
        raise CommandBusyError(device_id)
    command = {
        "command_id": f"CMD-{secrets.token_hex(6)}",
        "patient_code": patient_code,
        "status": "pendiente",
        "created_by": email,
        "created_at": _iso(now),
        "expires_at": _iso(now + PENDING_TTL),
    }
    if not repository.set_command(device_id, command):
        raise DeviceNotFoundError(device_id)
    return _command_public(command, now)


def current_order(device_id: str, role: str, email: str) -> dict | None:
    """La última orden del dispositivo con su estado actual, o None si nunca hubo una."""
    command = _device_for(device_id, role, email).get("command")
    return _command_public(command, _now()) if command else None


def cancel_order(device_id: str, role: str, email: str) -> dict | None:
    device = _device_for(device_id, role, email)
    command = device.get("command")
    if command:
        repository.update_command(
            device_id,
            command["command_id"],
            {"status": "cancelada", "completed_at": _iso(_now())},
            OPEN_STATUSES,
        )
        command = repository.get_device(device_id)["command"]
    return _command_public(command, _now()) if command else None


def poll_command(device_id: str, api_key: str | None) -> dict:
    """Lo que el ESP32 consulta cada pocos segundos: la orden a medir, o nada.

    Entregar la orden la pasa a «tomada» (con lo que deja de valer el plazo de 2 minutos y
    empieza el de 5 para medir). Si el aparato la vuelve a pedir porque perdió la respuesta,
    recibe la misma mientras siga vigente."""
    device = authenticate_device(device_id, api_key)
    command = device.get("command")
    if command:
        now = _now()
        status = _effective_status(command, now)
        if status == "pendiente":
            # Si otra consulta simultánea la tomó primero, da igual: queda «tomada» igual.
            repository.update_command(
                device_id,
                command["command_id"],
                {"status": "tomada", "taken_at": _iso(now)},
                ("pendiente",),
            )
            status = "tomada"
        if status == "tomada":
            return {
                "device_id": device_id,
                "command": {
                    "command_id": command["command_id"],
                    "patient_code": command["patient_code"],
                },
            }
    return {"device_id": device_id, "command": None}


def order_patient(device: dict, command_id: str | None) -> str | None:
    """Paciente de la orden `command_id` si es la vigente del dispositivo y sigue abierta."""
    command = device.get("command")
    if (
        command_id
        and command
        and command["command_id"] == command_id
        and _effective_status(command, _now()) in OPEN_STATUSES
    ):
        return command["patient_code"]
    return None


def complete_order(device_id: str, command_id: str, ts: str) -> None:
    """Cierra la orden cuando llega la medición que la cumple."""
    repository.update_command(
        device_id,
        command_id,
        {"status": "completada", "completed_at": _iso(_now()), "ts": ts},
        OPEN_STATUSES,
    )


def patient_codes(device_id: str, api_key: str | None) -> dict:
    """Códigos de paciente que el ESP32 ofrece en su lista, y la hora del servidor (UTC).

    Son los pacientes que vería el promotor del dispositivo. Solo códigos: sin nombres ni otros
    datos personales, porque la pantalla del equipo no los necesita.
    """
    device = authenticate_device(device_id, api_key)
    patients = patients_service.list_patients("promoter", device.get("promoter_email", ""))
    return {
        "device_id": device_id,
        "server_time": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "patients": [p["patient_code"] for p in patients],
    }
