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


class ApiKeyOut(BaseModel):
    device_id: str
    api_key: str
