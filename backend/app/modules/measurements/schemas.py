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
