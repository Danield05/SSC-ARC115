"""Modelos del contrato ESP32 -> API (ver CLAUDE.md)."""

from datetime import datetime

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


class MeasurementOut(BaseModel):
    record_id: str
    device_id: str
    ts: str
    weight_kg: float
    temp_c: float
    spo2: int
    bpm: int
    alert: bool
    bmi: float | None = None
    bmi_category: str | None = None


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
