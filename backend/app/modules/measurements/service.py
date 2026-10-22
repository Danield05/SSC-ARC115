"""Reglas de negocio del módulo measurements."""

from datetime import UTC, datetime
from decimal import Decimal

from app.core.config import get_settings
from app.core.security import verify_api_key
from app.modules.devices import repository as devices_repository
from app.modules.measurements import repository
from app.modules.measurements.schemas import BatchResult, MeasurementBatch, Record
from app.modules.patients import repository as patients_repository
from app.modules.patients import service as patients_service


class InvalidDeviceKeyError(Exception):
    """Clave ausente o inválida, dispositivo desconocido o dado de baja."""


def _iso_utc(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_alert(record: Record) -> bool:
    """Alerta por umbral (temperatura y SpO2), sin fiarse solo de la bandera del ESP32."""
    s = get_settings()
    return (
        record.temp_c <= s.temp_low_c or record.temp_c >= s.temp_high_c or record.spo2 < s.spo2_min
    )


def authenticate_device(device_id: str, api_key: str | None) -> dict:
    device = devices_repository.get_device(device_id)
    if (
        not api_key
        or device is None
        or not device.get("active", True)
        or not verify_api_key(api_key, device.get("api_key_hash", ""))
    ):
        raise InvalidDeviceKeyError(device_id)
    return device


def _to_item(device_id: str, record: Record, received_at: str) -> dict:
    return {
        "patient_code": record.patient_code,
        "ts": _iso_utc(record.ts),
        "record_id": record.record_id,
        "device_id": device_id,
        "weight_kg": Decimal(str(record.weight_kg)),
        "temp_c": Decimal(str(record.temp_c)),
        "spo2": record.spo2,
        "bpm": record.bpm,
        "alert": record.alert or is_alert(record),
        "received_at": received_at,
    }


def ingest(batch: MeasurementBatch, api_key: str | None) -> tuple[BatchResult, list[dict]]:
    """Guarda el lote. Devuelve el resultado del contrato y los registros nuevos guardados."""
    authenticate_device(batch.device_id, api_key)
    received_at = _iso_utc(datetime.now(UTC))
    saved: list[str] = []
    duplicates: list[str] = []
    new_items: list[dict] = []
    for record in batch.records:
        item = _to_item(batch.device_id, record, received_at)
        if repository.put_measurement(item):
            patients_repository.touch_patient(item["patient_code"], item["ts"], batch.device_id)
            saved.append(record.record_id)
            new_items.append(item)
        else:
            duplicates.append(record.record_id)
    return BatchResult(saved=saved, duplicates=duplicates), new_items


MAX_HISTORY = 1000
_FIRST_TS = "0000-01-01T00:00:00Z"
_LAST_TS = "9999-12-31T23:59:59Z"


class InvalidRangeError(Exception):
    """`from` es posterior a `to`."""


def history(
    patient_code: str,
    start: datetime | None,
    end: datetime | None,
    role: str,
    email: str,
) -> dict:
    """Mediciones de un paciente en un rango. Lanza PatientNotFoundError si el rol no lo ve."""
    patients_service.get_patient(patient_code, role, email)
    start_ts = _iso_utc(start) if start else _FIRST_TS
    end_ts = _iso_utc(end) if end else _LAST_TS
    if start_ts > end_ts:
        raise InvalidRangeError(patient_code)
    s = get_settings()
    return {
        "patient_code": patient_code,
        "thresholds": {
            "temp_low_c": s.temp_low_c,
            "temp_high_c": s.temp_high_c,
            "spo2_min": s.spo2_min,
        },
        "items": repository.list_measurements(patient_code, start_ts, end_ts, MAX_HISTORY),
    }
