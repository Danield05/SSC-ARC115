"""Modelos del contrato ESP32 -> API (ver CLAUDE.md)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Record(BaseModel):
    record_id: str = Field(min_length=1, max_length=64)
    patient_code: str = Field(pattern=r"^[A-Za-z0-9-]{1,32}$")
    ts: datetime
    weight_kg: float = Field(ge=0, le=500)
    temp_c: float = Field(ge=0, le=60)
    spo2: int = Field(ge=0, le=100)
    bpm: int = Field(ge=0, le=300)
    alert: bool


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
