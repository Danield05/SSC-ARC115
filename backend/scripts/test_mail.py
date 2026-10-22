"""Prueba el envío por Gmail paso a paso, para saber en qué punto falla.

Uso (desde backend/, con el entorno activado):
    python scripts/test_mail.py correo-destino@ejemplo.com
Pide la cuenta de Gmail y la contraseña de aplicación por teclado (o GMAIL_USER y
GMAIL_APP_PASSWORD en la sesión). Nunca se guardan en un archivo. Prueba el puerto 465 (SSL) y el
587 (STARTTLS) y muestra el error exacto de cada uno.
"""

import getpass
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage

HOST = "smtp.gmail.com"


def build(user: str, to: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = f"SSC-ARC115 <{user}>"
    msg["To"] = to
    msg["Subject"] = "Prueba de correo de SSC-ARC115"
    msg.set_content("Si lees esto, el envío por Gmail funciona.")
    return msg


def attempt(label: str, connect, user: str, password: str, to: str) -> bool:
    print(f"\n== {label}")
    try:
        with connect() as smtp:
            print("  conexión abierta")
            print("  login ... ", end="", flush=True)
            smtp.login(user, password)
            print("ok")
            smtp.send_message(build(user, to))
            print("  correo enviado")
        return True
    except Exception as e:  # noqa: BLE001 - es una herramienta de diagnóstico
        print(f"\n  FALLÓ: {type(e).__name__}: {e}")
        return False


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Uso: python scripts/test_mail.py correo-destino@ejemplo.com")
    to = sys.argv[1]
    user = os.environ.get("GMAIL_USER") or input("Cuenta de Gmail del sistema: ").strip()
    password = (
        os.environ.get("GMAIL_APP_PASSWORD") or getpass.getpass("Contraseña de aplicación: ")
    ).replace(" ", "")
    ctx = ssl.create_default_context()

    def ssl465():
        return smtplib.SMTP_SSL(HOST, 465, timeout=15, context=ctx)

    def starttls587():
        smtp = smtplib.SMTP(HOST, 587, timeout=15)
        smtp.starttls(context=ctx)
        return smtp

    ok465 = attempt("Puerto 465 (SSL, el que usa la API hoy)", ssl465, user, password, to)
    ok587 = attempt("Puerto 587 (STARTTLS)", starttls587, user, password, to)
    print(
        "\nResumen:",
        "465 " + ("OK" if ok465 else "falla"),
        "|",
        "587 " + ("OK" if ok587 else "falla"),
    )


if __name__ == "__main__":
    main()
