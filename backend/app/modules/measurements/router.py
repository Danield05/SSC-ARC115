"""Controlador HTTP del módulo measurements."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.modules.auth.dependencies import CurrentUser, require_roles
from app.modules.measurements import service
from app.modules.measurements.schemas import BatchResult, HistoryOut, MeasurementBatch
from app.modules.patients.service import PatientNotFoundError

router = APIRouter(prefix="/measurements", tags=["measurements"])
history_router = APIRouter(prefix="/patients", tags=["measurements"])

any_role = require_roles("admin", "viewer", "promoter")


@router.post("", response_model=BatchResult)
def receive_batch(body: MeasurementBatch, x_api_key: str | None = Header(default=None)):
    try:
        result, _ = service.ingest(body, x_api_key)
    except service.InvalidDeviceKeyError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clave de dispositivo inválida") from None
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
