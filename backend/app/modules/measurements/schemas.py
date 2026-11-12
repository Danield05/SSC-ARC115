"""Modelos del contrato ESP32 -> API (ver CLAUDE.md)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Record(BaseModel):
    record_id: str = Field(min_length=1, max_length=64)
    # Opcional: sin paciente (vacío, null o «SIN-ASIGNAR») la medición va a la bandeja «Sin
    # asignar», salvo que `command_id` sea el de la orden vigente del dispositivo.
    patient_code: str | None = Field(default=None, pattern=r"^[A-Za-z0-9-]{1,32}$")
    command_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9-]{1,32}$")
    ts: datetime
    weight_kg: float = Field(ge=0, le=500)
    temp_c: float = Field(ge=0, le=60)
    spo2: int = Field(ge=0, le=100)
    bpm: int = Field(ge=0, le=300)
    alert: bool

    @field_validator("patient_code", "command_id", mode="before")
    @classmethod
    def _blank_is_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value


class MeasurementBatch(BaseModel):
    device_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    records: list[Record] = Field(min_length=1, max_length=500)


class BatchResult(BaseModel):
    saved: list[str]
    duplicates: list[str]


ReviewStatus = Literal["confirmada", "falso_positivo", "artefacto"]


class ReviewIn(BaseModel):
    status: ReviewStatus
    note: str = Field(default="", max_length=200)


class ReviewOut(BaseModel):
    """Revisión de una alerta (estilo PhysioTag): quién la etiquetó, cuándo y con qué nota."""

    status: ReviewStatus
    note: str = ""
    reviewed_by: str
    reviewed_at: str


class MeasurementOut(BaseModel):
    record_id: str
    device_id: str
    ts: str
    # Cuándo la recibió el servidor (la hora del lote). Sirve para la trazabilidad: la diferencia
    # con `ts` es el tiempo que el dispositivo la guardó sin conexión.
    received_at: str | None = None
    weight_kg: float
    temp_c: float
    spo2: int
    bpm: int
    alert: bool
    bmi: float | None = None
    bmi_category: str | None = None
    review: ReviewOut | None = None


class UnassignedOut(BaseModel):
    """Una medición de la bandeja «Sin asignar»: guardada, pero sin paciente."""

    record_id: str
    device_id: str
    device_name: str = ""
    ts: str
    received_at: str | None = None
    weight_kg: float
    temp_c: float
    spo2: int
    bpm: int
    alert: bool


class AssignRef(BaseModel):
    device_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    ts: datetime


class AssignIn(BaseModel):
    patient_code: str = Field(pattern=r"^[A-Za-z0-9-]{1,32}$")
    items: list[AssignRef] = Field(min_length=1, max_length=100)


class AssignResult(BaseModel):
    assigned: list[str]  # ts (ISO-8601 UTC) de las mediciones movidas al paciente
    conflicts: list[str]  # el paciente ya tenía una medición con esa hora: no se movió
    not_found: list[str]  # ya asignada, inexistente o de un dispositivo que el rol no ve


class LatestAlert(BaseModel):
    patient_code: str
    ts: str


class AlertsSummaryOut(BaseModel):
    """Alertas de los últimos `days` días que el rol puede ver (tarjeta del resumen)."""

    days: int
    measurements: int  # mediciones del periodo (con paciente y sin asignar)
    alerts: int  # alertas de pacientes
    unassigned_alerts: int  # alertas que aún no tienen paciente
    latest: LatestAlert | None = None


class Thresholds(BaseModel):
    """Umbrales de alerta vigentes (los mismos que usa el servidor), para dibujarlos."""

    temp_low_c: float
    temp_high_c: float
    spo2_min: int


class HistoryOut(BaseModel):
    patient_code: str
    thresholds: Thresholds
    height_cm: float | None = None
    sex: str = ""
    age: int | None = None
    items: list[MeasurementOut]


class Stats(BaseModel):
    avg: float
    min: float
    max: float


class WindowOut(BaseModel):
    n: int
    weight_kg: Stats | None = None
    temp_c: Stats | None = None
    spo2: Stats | None = None
    bpm: Stats | None = None


class Latest(BaseModel):
    ts: str
    weight_kg: float
    temp_c: float
    spo2: int
    bpm: int


class BmiOut(BaseModel):
    value: float
    category: str | None = None
    height_cm: float


class WeightChange(BaseModel):
    vs_first_kg: float | None = None
    vs_first_pct: float | None = None
    vs_previous_kg: float | None = None


class TrendOut(BaseModel):
    per_day: float
    label: str


class Trends(BaseModel):
    weight_kg: TrendOut | None = None
    temp_c: TrendOut | None = None
    spo2: TrendOut | None = None
    bpm: TrendOut | None = None


class CorrelationOut(BaseModel):
    r: float
    n: int


class Correlations(BaseModel):
    temp_bpm: CorrelationOut | None = None


class SummaryOut(BaseModel):
    """Resumen del paciente. Sin mediciones: `count` en 0 y todo lo demás en null."""

    patient_code: str
    count: int
    first_ts: str | None = None
    last_ts: str | None = None
    latest: Latest | None = None
    bmi: BmiOut | None = None
    weight_change: WeightChange | None = None
    windows: dict[str, WindowOut] | None = None
    trend: Trends | None = None
    alert_pct: float | None = None
    correlation: Correlations | None = None
