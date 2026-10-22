"""Reglas de negocio del módulo patients."""

from datetime import UTC, datetime

from app.modules.devices import repository as devices_repository
from app.modules.patients import repository

CODE_PREFIX = "P-"
MAX_CODE_ATTEMPTS = 20


class PatientNotFoundError(Exception):
    pass


def to_public(patient: dict) -> dict:
    return {
        "patient_code": patient["patient_code"],
        "name": patient.get("name", ""),
        "dui": patient.get("dui", ""),
        "age": int(patient["age"]) if patient.get("age") is not None else None,
        "email": patient.get("email", ""),
        "phone": patient.get("phone", ""),
        "address": patient.get("address", ""),
        "first_seen": patient.get("first_seen", ""),
        "last_seen": patient.get("last_seen", ""),
        "device_ids": sorted(patient.get("device_ids", [])),
    }


def _my_device_ids(email: str) -> set[str]:
    return {
        d["device_id"]
        for d in devices_repository.list_devices()
        if d.get("promoter_email") == email
    }


def _visible(patient: dict, role: str, email: str, my_devices: set[str]) -> bool:
    """Admin y evaluador ven todo; el promotor, los que creó o que midieron sus equipos."""
    if role != "promoter":
        return True
    return patient.get("created_by") == email or bool(
        set(patient.get("device_ids", [])) & my_devices
    )


def list_patients(role: str, email: str) -> list[dict]:
    my_devices = _my_device_ids(email) if role == "promoter" else set()
    patients = [p for p in repository.list_patients() if _visible(p, role, email, my_devices)]
    return sorted((to_public(p) for p in patients), key=lambda p: p["patient_code"])


def create_patient(data: dict, email: str) -> dict:
    """Registra al paciente con un código asignado por el sistema (P-0001, P-0002…).

    Si el número ya está tomado (el dispositivo pudo haber enviado ese código antes), se pasa
    al siguiente.
    """
    fields = {k: v for k, v in data.items() if v not in (None, "")}
    for _ in range(MAX_CODE_ATTEMPTS):
        item = {
            **fields,
            "patient_code": f"{CODE_PREFIX}{repository.next_code_number():04d}",
            "created_by": email,
            "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if repository.create_patient(item):
            return to_public(item)
    raise RuntimeError("No se pudo asignar un código de paciente")


def update_patient(patient_code: str, changes: dict, role: str, email: str) -> dict:
    """Cambia solo los campos enviados; "" o None borran un dato opcional."""
    patient = repository.get_patient(patient_code)
    my_devices = _my_device_ids(email) if role == "promoter" else set()
    if patient is None or not _visible(patient, role, email, my_devices):
        raise PatientNotFoundError(patient_code)
    to_set = {}
    to_remove = []
    for field, value in changes.items():
        if field == "name":
            if value is not None:
                to_set["name"] = value
        elif value in (None, ""):
            to_remove.append(field)
        else:
            to_set[field] = value
    updated = repository.update_patient(patient_code, to_set, tuple(to_remove))
    if updated is None:
        raise PatientNotFoundError(patient_code)
    return to_public(updated)
