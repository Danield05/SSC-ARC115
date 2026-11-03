"""Controlador HTTP del módulo measurements."""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.modules.auth.dependencies import CurrentUser, require_roles
from app.modules.devices import service as devices_service
from app.modules.measurements import service
from app.modules.measurements.schemas import (
    BatchResult,
    HistoryOut,
    MeasurementBatch,
    SummaryOut,
)
from app.modules.notifications import service as notifications
from app.modules.patients.service import PatientNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/measurements", tags=["measurements"])
history_router = APIRouter(prefix="/patients", tags=["measurements"])

any_role = require_roles("admin", "viewer", "promoter")


@router.post("", response_model=BatchResult)
def receive_batch(body: MeasurementBatch, x_api_key: str | None = Header(default=None)):
    try:
        result, new_items, device = service.ingest(body, x_api_key)
    except devices_service.InvalidDeviceKeyError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clave de dispositivo inválida") from None
    if new_items and device.get("promoter_email"):
        # Un fallo de correo no puede dar error: el ESP32 reenviaría el lote, recibiría
        # `duplicates` y el correo se perdería para siempre.
        try:
            notifications.send_batch_report(
                device["promoter_email"],
                device.get("name") or device["device_id"],
                new_items,
                service.thresholds(),
            )
        except notifications.MailError:
            logger.error("No se envió el correo del lote de %s", device["device_id"])
    return result


@history_router.get("/{patient_code}/measurements", response_model=HistoryOut)
def patient_history(
    patient_code: str,
    user: CurrentUser = Depends(any_role),  # noqa: B008
    start: Annotated[datetime | None, Query(alias="from")] = None,
    end: Annotated[datetime | None, Query(alias="to")] = None,
):
    try:
        return service.history(patient_code, start, end, user.role, user.email)
    except PatientNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    except service.InvalidRangeError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La fecha inicial es posterior a la final"
        ) from None


@history_router.get("/{patient_code}/summary", response_model=SummaryOut)
def patient_summary(patient_code: str, user: CurrentUser = Depends(any_role)):  # noqa: B008
    try:
        return service.summary(patient_code, user.role, user.email)
    except PatientNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
