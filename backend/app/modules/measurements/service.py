"""Reglas de negocio del módulo measurements."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.config import get_settings
from app.core.constants import UNASSIGNED_CODE, unassigned_key
from app.modules.devices import service as devices_service
from app.modules.measurements import export, metrics, repository
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


def _storage_code(device: dict, record: Record) -> tuple[str, bool]:
    """Clave de paciente con la que se guarda el registro y si quedó asignado.

    Gana el código del propio registro. Si no trae (o trae «SIN-ASIGNAR»), se usa el paciente de
    la orden `command_id` si es la vigente del dispositivo; si tampoco, va a la bandeja
    «Sin asignar» de ese dispositivo."""
    code = record.patient_code
    if code and code.upper() == UNASSIGNED_CODE:
        code = None
    code = code or devices_service.order_patient(device, record.command_id)
    if code:
        return code, True
    return unassigned_key(device["device_id"]), False


def _to_item(device_id: str, patient_code: str, record: Record, received_at: str) -> dict:
    return {
        "patient_code": patient_code,
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
        code, assigned = _storage_code(device, record)
        item = _to_item(batch.device_id, code, record, received_at)
        if repository.put_measurement(item):
            if assigned:
                patients_repository.touch_patient(code, item["ts"], batch.device_id)
            if record.command_id:
                devices_service.complete_order(batch.device_id, record.command_id, item["ts"])
            saved.append(record.record_id)
            new_items.append(item)
        else:
            duplicates.append(record.record_id)
    return BatchResult(saved=saved, duplicates=duplicates), new_items, device


MAX_UNASSIGNED = 500  # por dispositivo


def unassigned(role: str, email: str) -> list[dict]:
    """Mediciones sin paciente de los dispositivos que el rol ve, de la más nueva a la más
    antigua. Las ya asignadas se quedan en la tabla (para detectar reenvíos) pero no se listan."""
    items = []
    for device in devices_service.list_devices(role, email):
        key = unassigned_key(device["device_id"])
        for m in repository.list_measurements(key, _FIRST_TS, _LAST_TS, MAX_UNASSIGNED):
            if "assigned_to" in m:
                continue
            items.append(
                {
                    **{k: m[k] for k in ("record_id", "device_id", "ts", "received_at")},
                    **{k: m[k] for k in ("weight_kg", "temp_c", "spo2", "bpm", "alert")},
                    "device_name": device["name"],
                }
            )
    return sorted(items, key=lambda m: m["ts"], reverse=True)


ALERT_WINDOW_DAYS = 7


def alerts_summary(role: str, email: str, days: int = ALERT_WINDOW_DAYS) -> dict:
    """Cuántas mediciones y cuántas alertas hubo en los últimos `days` días, para el resumen.

    Solo cuenta lo que el rol puede ver: sus pacientes (el promotor, los suyos) y, aparte, las
    mediciones sin asignar de sus dispositivos. `latest` es la alerta más reciente de un paciente
    (para enlazarla); None si solo hay alertas sin asignar o ninguna."""
    since = _iso_utc(datetime.now(UTC) - timedelta(days=days))
    measurements = alerts = unassigned_alerts = 0
    latest: dict | None = None
    for patient in patients_service.list_patients(role, email):
        code = patient["patient_code"]
        for m in repository.list_measurements(code, since, _LAST_TS, MAX_HISTORY):
            measurements += 1
            if m["alert"]:
                alerts += 1
                if latest is None or m["ts"] > latest["ts"]:
                    latest = {"patient_code": code, "ts": m["ts"]}
    for device in devices_service.list_devices(role, email):
        key = unassigned_key(device["device_id"])
        for m in repository.list_measurements(key, since, _LAST_TS, MAX_UNASSIGNED):
            if "assigned_to" in m:
                continue
            measurements += 1
            unassigned_alerts += bool(m["alert"])
    return {
        "days": days,
        "measurements": measurements,
        "alerts": alerts,
        "unassigned_alerts": unassigned_alerts,
        "latest": latest,
    }


def assign_unassigned(patient_code: str, refs: list[tuple[str, datetime]], role: str, email: str):
    """Mueve mediciones de la bandeja a un paciente. Devuelve (movidas, en conflicto, no
    encontradas), con los `ts` ISO-8601. Lanza PatientNotFoundError si el rol no ve al paciente.

    Cada una se reclama primero (atómico) y después se escribe en el paciente con la condición
    «no existe ya»: si el paciente tiene una medición con esa misma hora, se suelta y se reporta
    como conflicto sin tocar las demás."""
    patients_service.get_patient(patient_code, role, email)
    allowed = {d["device_id"] for d in devices_service.list_devices(role, email)}
    now = _iso_utc(datetime.now(UTC))
    assigned: list[str] = []
    conflicts: list[str] = []
    not_found: list[str] = []
    for device_id, when in refs:
        ts = _iso_utc(when)
        key = unassigned_key(device_id)
        if device_id not in allowed or not repository.claim_unassigned(
            key, ts, patient_code, email, now
        ):
            not_found.append(ts)
            continue
        original = repository.get_measurement(key, ts)
        item = {
            k: v
            for k, v in original.items()
            if k not in ("assigned_to", "assigned_by", "assigned_at")
        }
        item |= {"patient_code": patient_code, "assigned_by": email, "assigned_at": now}
        if not repository.put_measurement(item):
            repository.release_unassigned(key, ts)
            conflicts.append(ts)
            continue
        patients_repository.touch_patient(patient_code, ts, device_id)
        assigned.append(ts)
    return assigned, conflicts, not_found


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


class MeasurementNotFoundError(Exception):
    """No hay una medición con ese `ts` para el paciente."""


class NotAnAlertError(Exception):
    """Solo se revisan las mediciones con alerta."""


def review_alert(
    patient_code: str, ts: datetime, status: str, note: str, role: str, email: str
) -> dict:
    """Etiqueta una alerta (confirmada, falso positivo o artefacto) con una nota opcional.
    Mismo acceso que el historial: PatientNotFoundError si el rol no ve al paciente."""
    patients_service.get_patient(patient_code, role, email)
    key = _iso_utc(ts)
    measurement = repository.get_measurement(patient_code, key)
    if measurement is None:
        raise MeasurementNotFoundError(key)
    if not measurement["alert"]:
        raise NotAnAlertError(key)
    review = {
        "status": status,
        "note": note.strip(),
        "reviewed_by": email,
        "reviewed_at": _iso_utc(datetime.now(UTC)),
    }
    if not repository.set_review(patient_code, key, review):
        raise MeasurementNotFoundError(key)
    return review


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


EXPORT_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv; charset=utf-8",
}


class ExportForbiddenError(Exception):
    """Solo un administrador puede exportar con los datos personales del paciente."""


class ExportOptionsError(Exception):
    """`identified` y `anonymize` se contradicen: no se pueden pedir a la vez."""


def export_file(
    patient_code: str,
    fmt: str,
    start: datetime | None,
    end: datetime | None,
    role: str,
    email: str,
    identified: bool = False,
    anonymize: bool = False,
) -> tuple[bytes, str, str]:
    """Archivo del historial (contenido, tipo MIME, nombre). Mismas comprobaciones de acceso y
    de rango que el historial; los datos personales solo se incluyen si `identified` y es admin.

    Con `anonymize` el código real se cambia por un ID sustituto y las fechas por días desde la
    primera medición; cualquier rol que pueda ver al paciente puede pedirlo."""
    data = history(patient_code, start, end, role, email)
    if identified and role != "admin":
        raise ExportForbiddenError(patient_code)
    if identified and anonymize:
        raise ExportOptionsError(patient_code)
    code = export.pseudonym(patient_code, get_settings().jwt_secret) if anonymize else patient_code
    items = [{**m, "patient_code": code} for m in data["items"]]
    if anonymize:
        name = export.anonymous_filename(code, fmt)
    else:
        name = export.filename(patient_code, fmt, datetime.now(UTC).replace(tzinfo=None))
    if fmt == "csv":
        return export.build_csv(items, anonymize), EXPORT_TYPES["csv"], name
    personal = patients_service.get_patient(patient_code, role, email) if identified else None
    content = export.build_xlsx(
        code=code,
        age=data["age"],
        sex=data["sex"],
        height_cm=data["height_cm"],
        items=items,
        thresholds=data["thresholds"],
        identified=personal,
        anonymous=anonymize,
    )
    return content, EXPORT_TYPES["xlsx"], name
