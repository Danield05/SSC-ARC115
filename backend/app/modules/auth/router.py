"""Controlador HTTP del módulo auth: login y administración de usuarios."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.auth import service
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.modules.auth.schemas import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(tags=["auth"])

admin_only = require_roles("admin")


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    try:
        result = service.authenticate(body.email, body.password)
    except service.AuthNotConfiguredError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Servicio no configurado"
        ) from None
    if result is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos")
    token, user = result
    return {"access_token": token, "user": user}


@router.get("/auth/me", response_model=UserOut)
def me(user: CurrentUser = Depends(get_current_user)):  # noqa: B008
    return {"email": user.email, "role": user.role, "active": True, "created_at": ""}


@router.get("/users", response_model=list[UserOut])
def list_users(_: CurrentUser = Depends(admin_only)):  # noqa: B008
    return service.list_users()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, _: CurrentUser = Depends(admin_only)):  # noqa: B008
    try:
        return service.create_user(body.email, body.password, body.role)
    except service.UserExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un usuario con ese correo"
        ) from None


@router.patch("/users/{email}", response_model=UserOut)
def update_user(email: str, body: UserUpdate, admin: CurrentUser = Depends(admin_only)):  # noqa: B008
    try:
        return service.set_user_active(email.lower(), body.active, admin.email)
    except service.UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado") from None
    except service.SelfDeactivationError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "No puedes desactivar tu propia cuenta"
        ) from None
