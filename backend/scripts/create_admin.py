"""Crea (o reactiva) un usuario administrador. Es el primer usuario del sistema.

Local (con la base en marcha):
    python scripts/create_admin.py admin@example.com
En AWS: definir TABLE_USERS con el nombre real de la tabla, quitar DYNAMODB_ENDPOINT y usar
credenciales de AWS. La contraseña se pide por teclado (o ADMIN_PASSWORD); nunca va en un archivo.
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


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Uso: python scripts/create_admin.py [--local] correo@ejemplo.com")
    email = sys.argv[1].strip().lower()
    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Contraseña (mínimo 8): ")
    if len(password) < 8:
        sys.exit("La contraseña debe tener al menos 8 caracteres.")
    try:
        service.create_user(email, password, "admin")
    except service.UserExistsError:
        sys.exit(f"Ya existe un usuario con el correo {email}.")
    print(f"Administrador creado: {email}")


if __name__ == "__main__":
    main()
