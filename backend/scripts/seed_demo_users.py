"""Crea usuarios de ejemplo (promotor y evaluador) para probar los roles en local.

    python scripts/seed_demo_users.py --local

La contraseña se pide por teclado (o DEMO_PASSWORD) y es la misma para ambos usuarios.
El correo del promotor coincide con el del dispositivo de prueba (promotor@example.com).
No usar en AWS: allí los usuarios se crean con credenciales propias.
"""

import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if "--local" in sys.argv:
    sys.argv.remove("--local")
    os.environ.setdefault("DYNAMODB_ENDPOINT", "http://localhost:8001")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "local")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "local")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from app.modules.auth import service  # noqa: E402

DEMO_USERS = [("promotor@example.com", "promoter"), ("evaluador@example.com", "viewer")]


def main() -> None:
    if not os.environ.get("DYNAMODB_ENDPOINT"):
        sys.exit("Este script es solo para la base local: usa la opción --local.")
    password = os.environ.get("DEMO_PASSWORD") or getpass.getpass("Contraseña (mínimo 8): ")
    if len(password) < 8:
        sys.exit("La contraseña debe tener al menos 8 caracteres.")
    for email, role in DEMO_USERS:
        try:
            service.create_user(email, password, role)
            print(f"+ {email} ({role}) creado")
        except service.UserExistsError:
            print(f"= {email} ya existe")


if __name__ == "__main__":
    main()
