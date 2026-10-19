"""Muestra el contenido de las tablas de la base local (oculta hashes y contraseñas).

Uso: python scripts/show_tables.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DYNAMODB_ENDPOINT", "http://localhost:8001")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "local")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "local")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from app.core.dynamo import get_resource  # noqa: E402


def main() -> None:
    for table in get_resource().tables.all():
        items = table.scan()["Items"]
        print(f"== {table.name}: {len(items)} registros")
        for item in items:
            print("  ", {k: ("<oculto>" if "hash" in k else v) for k, v in item.items()})


if __name__ == "__main__":
    main()
