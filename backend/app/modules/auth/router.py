"""Controlador HTTP del módulo auth: sesión, contraseñas y administración de usuarios."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.auth import service
from app.modules.auth.dependencies import (
    CurrentUser,
    get_session_user,
    require_roles,
)
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageOut,
    TokenResponse,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(tags=["auth"])

admin_only = require_roles("admin")

_MAIL_FAILED = "No se pudo enviar el correo. Revisa la cuenta de correo del sistema."


def _user_not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")


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
def me(user: CurrentUser = Depends(get_session_user)):  # noqa: B008
    return service.get_public(user.email)


@router.post("/auth/forgot-password", response_model=MessageOut)
def forgot_password(body: ForgotPasswordRequest):
    service.request_password_reset(body.email)
    # La respuesta es la misma exista o no el correo, para no revelar quién tiene cuenta.
    return {"message": "Si el correo está registrado, te enviamos una contraseña provisional."}


@router.post("/auth/change-password", response_model=UserOut)
def change_password(body: ChangePasswordRequest, user: CurrentUser = Depends(get_session_user)):  # noqa: B008
    try:
        return service.change_password(user.email, body.current_password, body.new_password)
    except service.InvalidPasswordError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "La contraseña actual no es correcta"
        ) from None
    except service.SamePasswordError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "La contraseña nueva debe ser distinta de la actual"
        ) from None
    except service.UserNotFoundError:
        raise _user_not_found() from None


@router.get("/users", response_model=list[UserOut])
def list_users(_: CurrentUser = Depends(admin_only)):  # noqa: B008
    return service.list_users()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, _: CurrentUser = Depends(admin_only)):  # noqa: B008
    try:
        return service.invite_user(body.email, body.role, body.name)
    except service.UserExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un usuario con ese correo"
        ) from None
    except service.MailError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, _MAIL_FAILED) from None


@router.post("/users/{email}/resend-invite", response_model=UserOut)
def resend_invite(email: str, _: CurrentUser = Depends(admin_only)):  # noqa: B008
    try:
        return service.resend_invite(email.lower())
    except service.UserNotFoundError:
        raise _user_not_found() from None
    except service.NotPendingError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa persona ya activó su cuenta") from None
    except service.MailError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, _MAIL_FAILED) from None


@router.patch("/users/{email}", response_model=UserOut)
def update_user(email: str, body: UserUpdate, admin: CurrentUser = Depends(admin_only)):  # noqa: B008
    try:
        return service.update_user(
            email.lower(), body.active, body.role, admin.email, name=body.name, new_email=body.email
        )
    except service.UserNotFoundError:
        raise _user_not_found() from None
    except service.SelfEmailError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Tu propio correo lo cambia otro administrador"
        ) from None
    except service.UserExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un usuario con ese correo"
        ) from None
    except service.MailError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, _MAIL_FAILED) from None
    except service.SelfChangeError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "No puedes desactivar tu cuenta ni cambiar tu propio rol"
        ) from None
