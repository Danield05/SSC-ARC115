"""Aplicación FastAPI y adaptador para AWS Lambda (Mangum)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.core.config import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.devices.router import router as devices_router
from app.modules.measurements.router import history_router
from app.modules.measurements.router import router as measurements_router
from app.modules.notifications.router import router as notifications_router
from app.modules.patients.router import router as patients_router

settings = get_settings()

app = FastAPI(title="SSC-ARC115 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["authorization", "content-type", "x-api-key"],
)

for r in (
    auth_router,
    devices_router,
    patients_router,
    history_router,
    measurements_router,
    notifications_router,
):
    app.include_router(r)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


handler = Mangum(app)
