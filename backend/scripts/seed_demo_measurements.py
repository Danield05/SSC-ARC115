"""Carga un paciente de ejemplo con ~30 días de mediciones para ver el historial y las gráficas.

    python scripts/seed_demo_measurements.py --local

Solo para la base local. Crea el paciente "Paciente de ejemplo" (el código lo asigna el sistema) y
guarda una medición cada dos días con variaciones realistas; algunas salen de rango a propósito
(fiebre, hipotermia, SpO2 baja) para que se vea cómo se marcan las alertas. Las mediciones se
atribuyen al dispositivo de prueba ESP32-GP03-01, así que el promotor de ese dispositivo las ve.
"""

import math
import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if "--local" not in sys.argv:
    sys.exit("Este script es solo para la base local: usa la opción --local.")
sys.argv.remove("--local")
os.environ.setdefault("DYNAMODB_ENDPOINT", "http://localhost:8001")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "local")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "local")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from app.modules.measurements import repository as measurements_repository  # noqa: E402
from app.modules.patients import repository as patients_repository  # noqa: E402
from app.modules.patients import service as patients_service  # noqa: E402

DEVICE_ID = "ESP32-GP03-01"
DAYS = 30
STEP_DAYS = 2
# día (contando desde el inicio) -> (temperatura, spo2) que se salen del rango
ALERTS = {8: (38.4, 96), 16: (36.6, 90), 24: (34.8, 95)}


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    patient = patients_service.create_patient(
        {"name": "Paciente de ejemplo", "age": 54, "phone": "7000-0000"}, "demo@example.com"
    )
    code = patient["patient_code"]
    start = datetime.now(UTC).replace(hour=15, minute=0, second=0, microsecond=0) - timedelta(
        days=DAYS
    )
    saved = 0
    for day in range(0, DAYS + 1, STEP_DAYS):
        moment = start + timedelta(days=day)
        wave = math.sin(day / 4)
        temp, spo2 = ALERTS.get(day, (round(36.6 + 0.25 * wave, 1), round(97 + wave)))
        item = {
            "patient_code": code,
            "ts": iso(moment),
            "record_id": f"DEMO-{code}-{day:03d}",
            "device_id": DEVICE_ID,
            "weight_kg": Decimal(str(round(72.0 - day * 0.04 + 0.3 * wave, 1))),
            "temp_c": Decimal(str(temp)),
            "spo2": int(spo2),
            "bpm": int(round(76 + 6 * wave)),
            "alert": temp <= 35 or temp >= 38 or spo2 < 92,
            "received_at": iso(datetime.now(UTC)),
        }
        if measurements_repository.put_measurement(item):
            patients_repository.touch_patient(code, item["ts"], DEVICE_ID)
            saved += 1
    print(f"Paciente {code} creado con {saved} mediciones de ejemplo.")
    print(f"Abre http://localhost:5173/patients/{code}")


if __name__ == "__main__":
    main()
