"""Modelos de datos del módulo patients."""

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

PatientName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class PatientCreate(BaseModel):
    patient_code: str = Field(pattern=r"^[A-Za-z0-9-]{1,32}$")
    name: PatientName


class PatientUpdate(BaseModel):
    name: PatientName


class PatientOut(BaseModel):
    patient_code: str
    name: str = ""
    first_seen: str = ""
    last_seen: str = ""
    device_ids: list[str] = []
