"""Controlador HTTP del módulo devices."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.auth.dependencies import CurrentUser, require_roles
from app.modules.devices import service
from app.modules.devices.schemas import (
    ApiKeyOut,
    DeviceCreate,
    DeviceCreated,
    DeviceOut,
    DeviceUpdate,
)

router = APIRouter(prefix="/devices", tags=["devices"])

admin_only = require_roles("admin")
any_role = require_roles("admin", "viewer", "promoter")


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Dispositivo no encontrado")


@router.get("", response_model=list[DeviceOut])
def list_devices(user: CurrentUser = Depends(any_role)):  # noqa: B008
    return service.list_devices(user.role, user.email)


@router.post("", response_model=DeviceCreated, status_code=status.HTTP_201_CREATED)
def create_device(body: DeviceCreate, _: CurrentUser = Depends(admin_only)):  # noqa: B008
    try:
        device, api_key = service.create_device(body.device_id, body.name, body.promoter_email)
    except service.DeviceExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un dispositivo con ese identificador"
        ) from None
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
