"""Carga dos pacientes de ejemplo con ~30 días de mediciones para ver el historial, las gráficas,
la vista de monitor y el resumen.

    python scripts/seed_demo_measurements.py --local

Solo para la base local. Cada paciente (el código lo asigna el sistema) tiene su propia línea base
y una serie con situaciones para la demostración y las pruebas, inspiradas en el simulador de
señales de PhysioNet (solo la idea de tener episodios y artefactos; no se usa su código):

  * Paciente de ejemplo (adulta, 54 años): episodio febril de cuatro días en el que la temperatura
    y el pulso suben juntos (así la correlación se ve), una desaturación real, una hipotermia
    puntual, un artefacto (una sola lectura de SpO2 muy baja con el pulso normal, marcada como
    alerta) y un día con cuatro mediciones (para recorrer la línea de tiempo).
  * Segundo paciente (niño de 9 años, otra línea base): taquicardia puntual sin fiebre y un día con
    varias mediciones. Sirve para ver la categoría de IMC de menores (tablas de la OMS).

Las mediciones se atribuyen al dispositivo de prueba ESP32-GP03-01, así que el promotor de ese
dispositivo las ve. Todos los valores respetan los límites del contrato (modelo `Record`).
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

# Perfiles: ficha del paciente, línea base y situaciones por día (contando desde el inicio).
# Cada situación fija (temp, spo2, bpm); lo que no se fija sale de la línea base.
ADULT = {
    "patient": {
        "name": "Paciente de ejemplo",
        "age": 54,
        "sex": "F",
        "height_cm": 162,
        "phone": "7000-0000",
    },
    "base": {"temp": 36.6, "spo2": 97, "bpm": 76, "weight": 72.0, "weight_trend": -0.04},
    "events": {
        # Episodio febril: temperatura y pulso suben juntos durante cuatro días y bajan.
        16: {"temp": 37.7, "bpm": 88, "spo2": 96},
        18: {"temp": 38.4, "bpm": 99, "spo2": 95},
        20: {"temp": 38.9, "bpm": 104, "spo2": 95},
        22: {"temp": 37.9, "bpm": 90, "spo2": 96},
        # Desaturación real, con el pulso algo elevado.
        6: {"spo2": 90, "bpm": 92},
        # Hipotermia puntual.
        26: {"temp": 34.8},
        # Artefacto: SpO2 muy baja con el pulso normal (dedo mal puesto); el dispositivo la
        # marca como alerta porque está por debajo del umbral.
        12: {"spo2": 71, "bpm": 75},
    },
    # Día con varias mediciones (horas locales UTC): sirve para el deslizador.
    "busy_days": {28: (12, 15, 18, 21)},
}
CHILD = {
    "patient": {"name": "Segundo paciente", "age": 9, "sex": "M", "height_cm": 135},
    "base": {"temp": 36.9, "spo2": 98, "bpm": 88, "weight": 30.0, "weight_trend": 0.05},
    "events": {
        # Taquicardia puntual sin fiebre.
        14: {"bpm": 128},
    },
    "busy_days": {20: (13, 16, 19)},
}


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def series(profile: dict, start: datetime) -> list[dict]:
    """Mediciones del perfil: una cada STEP_DAYS a las 15:00 y varias en los días ocupados."""
    base = profile["base"]
    moments = {day: [15] for day in range(0, DAYS + 1, STEP_DAYS)}
    for day, hours in profile["busy_days"].items():
        moments[day] = list(hours)
    rows = []
    for day in sorted(moments):
        for hour in moments[day]:
            wave = math.sin(day / 4 + hour / 6)
            values = {
                "temp": round(base["temp"] + 0.2 * wave, 1),
                "spo2": round(base["spo2"] + 0.8 * wave),
                "bpm": round(base["bpm"] + 4 * wave),
                "weight": round(base["weight"] + base["weight_trend"] * day + 0.2 * wave, 1),
            }
            values.update(profile["events"].get(day, {}))
            moment = (start + timedelta(days=day)).replace(hour=hour)
            rows.append({"ts": iso(moment), "day": day, **values})
    return rows


def load(profile: dict, start: datetime) -> tuple[str, int]:
    patient = patients_service.create_patient(profile["patient"], "demo@example.com")
    code = patient["patient_code"]
    saved = 0
    for n, row in enumerate(series(profile, start)):
        item = {
            "patient_code": code,
            "ts": row["ts"],
            "record_id": f"DEMO-{code}-{n:03d}",
            "device_id": DEVICE_ID,
            "weight_kg": Decimal(str(row["weight"])),
            "temp_c": Decimal(str(row["temp"])),
            "spo2": int(row["spo2"]),
            "bpm": int(row["bpm"]),
            "alert": row["temp"] <= 35 or row["temp"] >= 38 or row["spo2"] < 92,
            "received_at": iso(datetime.now(UTC)),
        }
        if measurements_repository.put_measurement(item):
            patients_repository.touch_patient(code, item["ts"], DEVICE_ID)
            saved += 1
    return code, saved


def main() -> None:
    start = datetime.now(UTC).replace(hour=15, minute=0, second=0, microsecond=0) - timedelta(
        days=DAYS
    )
    for profile in (ADULT, CHILD):
        code, saved = load(profile, start)
        print(f"Paciente {code} ({profile['patient']['name']}): {saved} mediciones de ejemplo.")
        print(f"  Historial: http://localhost:5173/patients/{code}")
        print(f"  Monitor:   http://localhost:5173/patients/{code}/monitor")


if __name__ == "__main__":
    main()
