"""Controlador HTTP del módulo measurements."""

import logging
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status

from app.modules.auth.dependencies import CurrentUser, require_roles
from app.modules.devices import service as devices_service
from app.modules.measurements import service
from app.modules.measurements.schemas import (
    AlertsSummaryOut,
    AssignIn,
    AssignResult,
    BatchResult,
    HistoryOut,
    MeasurementBatch,
    ReviewIn,
    ReviewOut,
    SummaryOut,
    UnassignedOut,
)
from app.modules.notifications import service as notifications
from app.modules.patients.service import PatientNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/measurements", tags=["measurements"])
history_router = APIRouter(prefix="/patients", tags=["measurements"])

any_role = require_roles("admin", "viewer", "promoter")
reviewer_role = require_roles("admin", "promoter")  # el evaluador (viewer) solo lee


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


@router.get("/alerts-summary", response_model=AlertsSummaryOut)
def alerts_summary(user: CurrentUser = Depends(any_role)):  # noqa: B008
    """Tarjeta «Alertas» del resumen: las de los últimos 7 días que el rol puede ver."""
    return service.alerts_summary(user.role, user.email)


@router.get("/unassigned", response_model=list[UnassignedOut])
def list_unassigned(user: CurrentUser = Depends(any_role)):  # noqa: B008
    """Bandeja «Sin asignar»: mediciones de sus dispositivos que aún no tienen paciente."""
    return service.unassigned(user.role, user.email)


@router.post("/unassigned/assign", response_model=AssignResult)
def assign_unassigned(body: AssignIn, user: CurrentUser = Depends(reviewer_role)):  # noqa: B008
    try:
        assigned, conflicts, not_found = service.assign_unassigned(
            body.patient_code,
            [(i.device_id, i.ts) for i in body.items],
            user.role,
            user.email,
        )
    except PatientNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    return {"assigned": assigned, "conflicts": conflicts, "not_found": not_found}


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


@history_router.patch("/{patient_code}/measurements/{ts}/review", response_model=ReviewOut)
def review_alert(
    patient_code: str,
    ts: datetime,
    body: ReviewIn,
    user: CurrentUser = Depends(reviewer_role),  # noqa: B008
):
    try:
        return service.review_alert(patient_code, ts, body.status, body.note, user.role, user.email)
    except PatientNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    except service.MeasurementNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medición no encontrada") from None
    except service.NotAnAlertError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Solo se revisan las mediciones con alerta"
        ) from None


@history_router.get("/{patient_code}/summary", response_model=SummaryOut)
def patient_summary(patient_code: str, user: CurrentUser = Depends(any_role)):  # noqa: B008
    try:
        return service.summary(patient_code, user.role, user.email)
    except PatientNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None


@history_router.get("/{patient_code}/export")
def patient_export(
    patient_code: str,
    user: CurrentUser = Depends(any_role),  # noqa: B008
    fmt: Annotated[Literal["xlsx", "csv"], Query(alias="format")] = "xlsx",
    start: Annotated[datetime | None, Query(alias="from")] = None,
    end: Annotated[datetime | None, Query(alias="to")] = None,
    identified: bool = False,
    anonymize: bool = False,
):
    try:
        content, media_type, name = service.export_file(
            patient_code, fmt, start, end, user.role, user.email, identified, anonymize
        )
    except PatientNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    except service.InvalidRangeError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La fecha inicial es posterior a la final"
        ) from None
    except service.ExportForbiddenError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Solo un administrador puede exportar datos personales"
        ) from None
    except service.ExportOptionsError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "No se puede pedir a la vez la exportación identificada y la anonimizada",
        ) from None
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
