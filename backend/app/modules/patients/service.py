"""Reglas de negocio del módulo patients."""

from datetime import UTC, datetime

from app.modules.devices import repository as devices_repository
from app.modules.patients import repository


class PatientExistsError(Exception):
    pass


class PatientNotFoundError(Exception):
    pass


def to_public(patient: dict) -> dict:
    return {
        "patient_code": patient["patient_code"],
        "name": patient.get("name", ""),
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


def create_patient(patient_code: str, name: str, email: str) -> dict:
    item = {
        "patient_code": patient_code,
        "name": name,
        "created_by": email,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if not repository.create_patient(item):
        raise PatientExistsError(patient_code)
    return to_public(item)


def update_name(patient_code: str, name: str, role: str, email: str) -> dict:
    patient = repository.get_patient(patient_code)
    my_devices = _my_device_ids(email) if role == "promoter" else set()
    if patient is None or not _visible(patient, role, email, my_devices):
        raise PatientNotFoundError(patient_code)
    updated = repository.set_name(patient_code, name)
    if updated is None:
        raise PatientNotFoundError(patient_code)
    return to_public(updated)
