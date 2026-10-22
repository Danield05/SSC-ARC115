"""Controlador HTTP del módulo patients."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.auth.dependencies import CurrentUser, require_roles
from app.modules.patients import service
from app.modules.patients.schemas import PatientCreate, PatientOut, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])

any_role = require_roles("admin", "viewer", "promoter")
can_write = require_roles("admin", "promoter")


@router.get("", response_model=list[PatientOut])
def list_patients(user: CurrentUser = Depends(any_role)):  # noqa: B008
    return service.list_patients(user.role, user.email)


@router.get("/{patient_code}", response_model=PatientOut)
def get_patient(patient_code: str, user: CurrentUser = Depends(any_role)):  # noqa: B008
    try:
        return service.get_patient(patient_code, user.role, user.email)
    except service.PatientNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(body: PatientCreate, user: CurrentUser = Depends(can_write)):  # noqa: B008
    return service.create_patient(body.model_dump(), user.email)


@router.patch("/{patient_code}", response_model=PatientOut)
def update_patient(
    patient_code: str,
    body: PatientUpdate,
    user: CurrentUser = Depends(can_write),  # noqa: B008
):
    try:
        return service.update_patient(
            patient_code, body.model_dump(exclude_unset=True), user.role, user.email
        )
    except service.PatientNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado") from None
