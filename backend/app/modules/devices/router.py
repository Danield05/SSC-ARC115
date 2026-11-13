"""Controlador HTTP del módulo devices."""

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.modules.auth.dependencies import CurrentUser, require_roles
from app.modules.devices import service
from app.modules.devices.schemas import (
    ApiKeyOut,
    CommandPollOut,
    DeviceCreate,
    DeviceCreated,
    DeviceOut,
    DevicePatientsOut,
    DeviceUpdate,
    MeasureIn,
    MeasureOrderOut,
)
from app.modules.patients.service import PatientNotFoundError

router = APIRouter(prefix="/devices", tags=["devices"])

admin_only = require_roles("admin")
any_role = require_roles("admin", "viewer", "promoter")
measurer_role = require_roles("admin", "promoter")  # el evaluador (viewer) solo lee


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Dispositivo no encontrado")


@router.get("", response_model=list[DeviceOut])
def list_devices(user: CurrentUser = Depends(any_role)):  # noqa: B008
    return service.list_devices(user.role, user.email)


@router.post("", response_model=DeviceCreated, status_code=status.HTTP_201_CREATED)
def create_device(body: DeviceCreate, _: CurrentUser = Depends(admin_only)):  # noqa: B008
    device, api_key = service.create_device(body.name, body.promoter_email)
    return {**device, "api_key": api_key}


@router.patch("/{device_id}", response_model=DeviceOut)
def update_device(device_id: str, body: DeviceUpdate, _: CurrentUser = Depends(admin_only)):  # noqa: B008
    try:
        return service.update_device(device_id, body.model_dump())
    except service.DeviceNotFoundError:
        raise _not_found() from None


@router.post("/{device_id}/rotate-key", response_model=ApiKeyOut)
def rotate_key(device_id: str, _: CurrentUser = Depends(admin_only)):  # noqa: B008
    try:
        return {"device_id": device_id, "api_key": service.rotate_api_key(device_id)}
    except service.DeviceNotFoundError:
        raise _not_found() from None


@router.post("/{device_id}/measure", response_model=MeasureOrderOut, status_code=201)
def start_measure(
    device_id: str,
    body: MeasureIn,
    user: CurrentUser = Depends(measurer_role),  # noqa: B008
):
    """«Medir a este paciente»: deja la orden para que el ESP32 la tome. Admin y promotor."""
    try:
        return service.create_measure_order(device_id, body.patient_code, user.role, user.email)
    except service.DeviceNotFoundError:
        raise _not_found() from None
    except PatientNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
    except service.CommandBusyError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "El aparato ya está midiendo a otro paciente"
        ) from None


@router.get("/{device_id}/measure", response_model=MeasureOrderOut | None)
def measure_status(device_id: str, user: CurrentUser = Depends(any_role)):  # noqa: B008
    """Estado de la última orden, para la ventana de carga de la web."""
    try:
        return service.current_order(device_id, user.role, user.email)
    except service.DeviceNotFoundError:
        raise _not_found() from None


@router.delete("/{device_id}/measure", response_model=MeasureOrderOut | None)
def cancel_measure(device_id: str, user: CurrentUser = Depends(measurer_role)):  # noqa: B008
    try:
        return service.cancel_order(device_id, user.role, user.email)
    except service.DeviceNotFoundError:
        raise _not_found() from None


@router.get("/{device_id}/command", response_model=CommandPollOut)
def device_command(device_id: str, x_api_key: str | None = Header(default=None)):
    """Consulta del ESP32: ¿hay que medir a alguien? Se autentica con `x-api-key`."""
    try:
        return service.poll_command(device_id, x_api_key)
    except service.InvalidDeviceKeyError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clave de dispositivo inválida") from None


@router.get("/{device_id}/patients", response_model=DevicePatientsOut)
def device_patients(device_id: str, x_api_key: str | None = Header(default=None)):
    """Lista de códigos para el ESP32. Se autentica con `x-api-key`, no con JWT."""
    try:
        return service.patient_codes(device_id, x_api_key)
    except service.InvalidDeviceKeyError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clave de dispositivo inválida") from None
