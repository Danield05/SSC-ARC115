"""Crea las 3 tablas en la base local y carga datos de prueba.

Uso (con el servidor local en marcha: `moto_server -p 8001`):
    python scripts/create_tables.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DYNAMODB_ENDPOINT", "http://localhost:8001")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "local")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "local")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from app.core.config import get_settings  # noqa: E402
from app.core.dynamo import get_resource  # noqa: E402
from app.core.security import hash_api_key  # noqa: E402

DEV_API_KEY = "dev-key-local"


def create(name: str, keys: list[tuple[str, str]]):
    db = get_resource()
    if name in [t.name for t in db.tables.all()]:
        print(f"= {name} ya existe")
        return db.Table(name)
    types = {"HASH": "HASH", "RANGE": "RANGE"}
    table = db.create_table(
        TableName=name,
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[{"AttributeName": k, "AttributeType": "S"} for k, _ in keys],
        KeySchema=[{"AttributeName": k, "KeyType": types[t]} for k, t in keys],
    )
    table.wait_until_exists()
    print(f"+ {name} creada")
    return table


def main() -> None:
    s = get_settings()
    devices = create(s.table_devices, [("device_id", "HASH")])
    create(s.table_patients, [("patient_code", "HASH")])
    create(s.table_measurements, [("patient_code", "HASH"), ("ts", "RANGE")])
    devices.put_item(
        Item={
            "device_id": "ESP32-GP03-01",
            "api_key_hash": hash_api_key(DEV_API_KEY),
            "promoter_email": "promotor@example.com",
            "name": "Dispositivo de desarrollo",
        }
    )
    print(f"Dispositivo de prueba listo: ESP32-GP03-01 / x-api-key: {DEV_API_KEY}")


if __name__ == "__main__":
    main()
