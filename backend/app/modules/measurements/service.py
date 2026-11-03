"""Reglas de negocio del módulo measurements."""

from datetime import UTC, datetime
from decimal import Decimal

from app.core.config import get_settings
from app.modules.devices import service as devices_service
from app.modules.measurements import metrics, repository
from app.modules.measurements.schemas import BatchResult, MeasurementBatch, Record
from app.modules.patients import repository as patients_repository
from app.modules.patients import service as patients_service
from app.modules.patients.bmi import bmi, bmi_category


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


def ingest(batch: MeasurementBatch, api_key: str | None) -> tuple[BatchResult, list[dict], dict]:
    """Guarda el lote. Devuelve el resultado del contrato, los registros nuevos y el dispositivo."""
    device = devices_service.authenticate_device(batch.device_id, api_key)
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
    return BatchResult(saved=saved, duplicates=duplicates), new_items, device


def thresholds() -> dict:
    s = get_settings()
    return {"temp_low_c": s.temp_low_c, "temp_high_c": s.temp_high_c, "spo2_min": s.spo2_min}


MAX_HISTORY = 1000
_FIRST_TS = "0000-01-01T00:00:00Z"
_LAST_TS = "9999-12-31T23:59:59Z"


class InvalidRangeError(Exception):
    """`from` es posterior a `to`."""


def _with_bmi(measurement: dict, patient: dict) -> dict:
    value = bmi(measurement["weight_kg"], patient["height_cm"])
    return {
        **measurement,
        "bmi": value,
        "bmi_category": bmi_category(value, patient["age"], patient["sex"]),
    }


def history(
    patient_code: str,
    start: datetime | None,
    end: datetime | None,
    role: str,
    email: str,
) -> dict:
    """Mediciones de un paciente en un rango. Lanza PatientNotFoundError si el rol no lo ve."""
    patient = patients_service.get_patient(patient_code, role, email)
    start_ts = _iso_utc(start) if start else _FIRST_TS
    end_ts = _iso_utc(end) if end else _LAST_TS
    if start_ts > end_ts:
        raise InvalidRangeError(patient_code)
    measurements = repository.list_measurements(patient_code, start_ts, end_ts, MAX_HISTORY)
    return {
        "patient_code": patient_code,
        "thresholds": thresholds(),
        "height_cm": patient["height_cm"],
        "sex": patient["sex"],
        "age": patient["age"],
        "items": [_with_bmi(m, patient) for m in measurements],
    }


def _trend(variable: str, items: list[dict]) -> dict | None:
    points = [(metrics.parse_ts(m["ts"]), m[variable]) for m in items]
    per_day = metrics.slope_per_day(points)
    if per_day is None:
        return None
    return {"per_day": round(per_day, 3), "label": metrics.trend_label(variable, per_day)}


def summary(patient_code: str, role: str, email: str) -> dict:
    """Métricas del paciente con sus últimas MAX_HISTORY mediciones. Lanza PatientNotFoundError
    si el rol no lo ve (igual que el historial)."""
    patient = patients_service.get_patient(patient_code, role, email)
    items = repository.list_measurements(patient_code, _FIRST_TS, _LAST_TS, MAX_HISTORY)
    if not items:
        return {"patient_code": patient_code, "count": 0}
    last = items[-1]
    bmi_value = bmi(last["weight_kg"], patient["height_cm"])
    pairs = [(m["temp_c"], m["bpm"]) for m in items]
    r = metrics.pearson([float(t) for t, _ in pairs], [float(b) for _, b in pairs])
    windows = {}
    for days in metrics.WINDOW_DAYS:
        chosen = metrics.window(items, days)
        windows[str(days)] = {"n": len(chosen)} | {
            v: metrics.stats([m[v] for m in chosen]) for v in metrics.VARIABLES
        }
    return {
        "patient_code": patient_code,
        "count": len(items),
        "first_ts": items[0]["ts"],
        "last_ts": last["ts"],
        "latest": {k: last[k] for k in ("ts", "weight_kg", "temp_c", "spo2", "bpm")},
        "bmi": None
        if bmi_value is None
        else {
            "value": bmi_value,
            "category": bmi_category(bmi_value, patient["age"], patient["sex"]),
            "height_cm": patient["height_cm"],
        },
        "weight_change": metrics.weight_change(items),
        "windows": windows,
        "trend": {v: _trend(v, items) for v in metrics.VARIABLES},
        "alert_pct": metrics.alert_percentage(items),
        "correlation": {"temp_bpm": None if r is None else {"r": round(r, 2), "n": len(items)}},
    }
