"""Reglas de negocio del módulo notifications: envío de correo por SMTP de Gmail."""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings
from app.modules.notifications import templates

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_TIMEOUT = 10


class MailError(Exception):
    """El correo no se pudo enviar (cuenta sin configurar o fallo del servidor SMTP)."""


def send_email(to: str, subject: str, text: str, html: str) -> None:
    s = get_settings()
    if not (s.gmail_user and s.gmail_app_password):
        if s.mail_console:
            # Solo perfil local: sirve para probar los flujos sin una cuenta de Gmail.
            logger.warning("CORREO (consola) a %s · %s\n%s", to, subject, text)
            return
        raise MailError("GMAIL_USER y GMAIL_APP_PASSWORD no están configurados")
    msg = EmailMessage()
    msg["From"] = f"SSC-ARC115 <{s.gmail_user}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP_SSL(
            SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT, context=ssl.create_default_context()
        ) as smtp:
            smtp.login(s.gmail_user, s.gmail_app_password)
            smtp.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        logger.error("Fallo al enviar correo a %s: %s", to, type(e).__name__)
        raise MailError(str(e)) from e


def send_invitation(to: str, name: str, role_label: str, temp_password: str) -> None:
    subject, text, html = templates.invitation(
        name, to, role_label, temp_password, get_settings().allowed_origin
    )
    send_email(to, subject, text, html)


def send_batch_report(to: str, device_name: str, items: list[dict], thresholds: dict) -> None:
    subject, text, html = templates.measurement_batch(
        device_name, items, thresholds, get_settings().allowed_origin
    )
    send_email(to, subject, text, html)


def send_password_reset(to: str, name: str, temp_password: str, minutes: int) -> None:
    subject, text, html = templates.password_reset(
        name, temp_password, minutes, get_settings().allowed_origin
    )
    send_email(to, subject, text, html)
