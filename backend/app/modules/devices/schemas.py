"""Modelos de datos del módulo devices."""

from pydantic import BaseModel, Field

from app.modules.auth.schemas import Email


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    promoter_email: Email


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    promoter_email: Email | None = None
    active: bool | None = None


class DeviceOut(BaseModel):
    device_id: str
    name: str
    promoter_email: str
    active: bool
    created_at: str


class DeviceCreated(DeviceOut):
    api_key: str


class DevicePatientsOut(BaseModel):
    device_id: str
    server_time: str
    patients: list[str]


class MeasureIn(BaseModel):
    patient_code: str = Field(pattern=r"^[A-Za-z0-9-]{1,32}$")


class MeasureOrderOut(BaseModel):
    """Orden «Medir a este paciente» y en qué punto va (la web la consulta mientras espera)."""

    command_id: str
    patient_code: str
    # pendiente → tomada → completada; o cancelada / expirada.
    status: str
    created_at: str
    expires_at: str
    taken_at: str | None = None
    completed_at: str | None = None
    ts: str | None = None  # hora de la medición que la completó


class CommandOut(BaseModel):
    command_id: str
    patient_code: str


class CommandPollOut(BaseModel):
    device_id: str
    command: CommandOut | None = None


class ApiKeyOut(BaseModel):
    device_id: str
    api_key: str
