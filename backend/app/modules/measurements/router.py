"""Controlador HTTP del módulo measurements."""

from fastapi import APIRouter, Header, HTTPException, status

from app.modules.measurements import service
from app.modules.measurements.schemas import BatchResult, MeasurementBatch

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.post("", response_model=BatchResult)
def receive_batch(body: MeasurementBatch, x_api_key: str | None = Header(default=None)):
    try:
        result, _ = service.ingest(body, x_api_key)
    except service.InvalidDeviceKeyError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clave de dispositivo inválida") from None
    return result
