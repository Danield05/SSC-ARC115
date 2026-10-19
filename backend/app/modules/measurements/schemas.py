"""Modelos del contrato ESP32 -> API (ver CLAUDE.md)."""

from datetime import datetime

from pydantic import BaseModel, Field


class Record(BaseModel):
    record_id: str
    patient_code: str
    ts: datetime
    weight_kg: float = Field(ge=0)
    temp_c: float
    spo2: int = Field(ge=0, le=100)
    bpm: int = Field(ge=0)
    alert: bool


class MeasurementBatch(BaseModel):
    device_id: str
    records: list[Record] = Field(min_length=1)


class BatchResult(BaseModel):
    saved: list[str]
    duplicates: list[str]
