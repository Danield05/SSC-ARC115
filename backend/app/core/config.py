"""Configuración leída de variables de entorno (ver .env.example)."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    table_devices: str
    table_patients: str
    table_measurements: str
    table_users: str
    gmail_user: str
    gmail_app_password: str
    allowed_origin: str
    jwt_secret: str
    temp_low_c: float
    temp_high_c: float
    spo2_min: int
    log_level: str


@lru_cache
def get_settings() -> Settings:
    env = os.environ.get
    return Settings(
        table_devices=env("TABLE_DEVICES", "devices"),
        table_patients=env("TABLE_PATIENTS", "patients"),
        table_measurements=env("TABLE_MEASUREMENTS", "measurements"),
        table_users=env("TABLE_USERS", "users"),
        gmail_user=env("GMAIL_USER", ""),
        gmail_app_password=env("GMAIL_APP_PASSWORD", ""),
        allowed_origin=env("ALLOWED_ORIGIN", "http://localhost:5173"),
        jwt_secret=env("JWT_SECRET", ""),
        temp_low_c=float(env("TEMP_LOW_C", "35")),
        temp_high_c=float(env("TEMP_HIGH_C", "38")),
        spo2_min=int(env("SPO2_MIN", "92")),
        log_level=env("LOG_LEVEL", "INFO"),
    )
