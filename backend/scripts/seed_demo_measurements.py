"""Carga dos pacientes de ejemplo con ~30 días de mediciones para ver el historial, las gráficas,
la vista de monitor y el resumen.

    python scripts/seed_demo_measurements.py --local

Solo para la base local. Cada paciente (el código lo asigna el sistema) tiene su propia línea base
y una serie con situaciones para la demostración y las pruebas, inspiradas en el simulador de
señales de PhysioNet (solo la idea de tener episodios y artefactos; no se usa su código):

  * Paciente de ejemplo (adulta, 54 años): episodio febril de cuatro días en el que la temperatura
    y el pulso suben juntos (así la correlación se ve), un episodio de desaturación de dos
    mediciones seguidas, una hipotermia puntual, una bradicardia (sin alerta: el pulso no tiene
    umbral, solo se ve como desvío frente a su línea base), un artefacto (una sola lectura de SpO2
    muy baja con el pulso normal, marcada como alerta) y un día con cuatro mediciones (para
    recorrer la línea de tiempo).
  * Segundo paciente (niño de 9 años, otra línea base): taquicardia puntual sin fiebre y un día con
    varias mediciones. Sirve para ver la categoría de IMC de menores (tablas de la OMS).

Los valores llevan una variación natural pequeña y reproducible (semilla fija), a la manera del
generador de señales sintéticas con ruido de PhysioNet, para que las series no sean curvas
perfectas y la franja de colores tenga algo que mostrar. El ruido nunca cruza un umbral: las
alertas son solo las de las situaciones de arriba.

Cada paciente tiene también un periodo sin conexión: el dispositivo guarda esas mediciones y
las envía juntas (un solo lote) cuando vuelve internet. Así la pestaña de trazabilidad muestra
cuándo se midió cada una y cuándo llegó a la nube. Las demás llegan segundos después de medirse.

Algunas alertas del paciente de ejemplo ya vienen revisadas (confirmada y artefacto) y otras
quedan pendientes (también una de las dos de cada episodio, para ver la revisión parcial).

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
# Variación aleatoria máxima (±) de cada valor, sin cruzar nunca un umbral de alerta.
NOISE = {"temp": 0.05, "spo2": 0.4, "bpm": 1.5, "weight": 0.05}
DAYS = 30
STEP_DAYS = 2

# Perfiles: ficha del paciente, línea base y situaciones por día (contando desde el inicio).
# Cada situación fija (temp, spo2, bpm); lo que no se fija sale de la línea base.
ADULT = {
    "noise_seed": 3,
    "patient": {
        "name": "Paciente de ejemplo",
        "age": 54,
        "sex": "F",
        "height_cm": 162,
        "phone": "7000-0000",
    },
    "base": {"temp": 36.6, "spo2": 97, "bpm": 76, "weight": 72.0, "weight_trend": -0.02},
    "events": {
        # Episodio febril: temperatura y pulso suben juntos durante cuatro días y bajan.
        16: {"temp": 37.7, "bpm": 88, "spo2": 96},
        18: {"temp": 38.4, "bpm": 99, "spo2": 95},
        20: {"temp": 38.9, "bpm": 104, "spo2": 95},
        22: {"temp": 37.9, "bpm": 90, "spo2": 96},
        # Episodio de desaturación de dos mediciones seguidas, con el pulso algo elevado.
        4: {"spo2": 91, "bpm": 88},
        6: {"spo2": 90, "bpm": 92},
        # Bradicardia puntual: sin alerta (el pulso no tiene umbral), se ve como desvío.
        8: {"bpm": 50},
        # Hipotermia puntual.
        26: {"temp": 34.8},
        # Artefacto: SpO2 muy baja con el pulso normal (dedo mal puesto); el dispositivo la
        # marca como alerta porque está por debajo del umbral.
        12: {"spo2": 71, "bpm": 75},
    },
    # Día con varias mediciones (horas locales UTC): sirve para el deslizador.
    "busy_days": {28: (12, 15, 18, 21)},
    # Sin conexión de los días 10 a 12 (incluye el artefacto); se envían juntas el día 13.
    "offline": [(10, 12, 13)],
    # Alertas ya revisadas (día: etiqueta y nota); las demás quedan pendientes.
    "reviews": {
        6: ("confirmada", "Desaturación real, con el pulso algo elevado."),
        12: ("artefacto", "SpO2 de 71 % con el pulso normal: el dedo estaba mal puesto."),
        18: ("confirmada", "Dentro del episodio febril."),
    },
}
CHILD = {
    "noise_seed": 7,
    "patient": {"name": "Segundo paciente", "age": 9, "sex": "M", "height_cm": 135},
    "base": {"temp": 36.9, "spo2": 98, "bpm": 88, "weight": 30.0, "weight_trend": 0.02},
    "events": {
        # Taquicardia puntual sin fiebre.
        14: {"bpm": 128},
    },
    "busy_days": {20: (13, 16, 19)},
    # Sin conexión de los días 14 a 16 (incluye la taquicardia); se envían juntas el día 17.
    "offline": [(14, 16, 17)],
}


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


SYNC_DELAY = timedelta(seconds=20)


def received_at(profile: dict, start: datetime, day: int, moment: datetime) -> datetime:
    """Cuándo llegó la medición a la nube: segundos después de medirla, salvo en un periodo sin
    conexión, donde llega junta con las demás cuando vuelve internet (8:00 del día de envío)."""
    for first, last, upload_day in profile.get("offline", ()):
        if first <= day <= last:
            return (start + timedelta(days=upload_day)).replace(hour=8, minute=0, second=0)
    return moment + SYNC_DELAY


def jitter(seed: int, day: int, hour: int, key: str) -> float:
    """Número pseudoaleatorio entre -1 y 1 que depende solo de sus argumentos: el mismo ruido en
    cada carga, sin generadores aleatorios."""
    x = math.sin(seed * 12.9898 + day * 78.233 + hour * 37.719 + sum(map(ord, key)) * 4.1414)
    x *= 43758.5453
    return 2 * (x - math.floor(x)) - 1


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
            noise = {
                key: size * jitter(profile["noise_seed"], day, hour, key)
                for key, size in NOISE.items()
            }
            values = {
                "temp": round(base["temp"] + 0.2 * wave + noise["temp"], 1),
                "spo2": round(base["spo2"] + 0.8 * wave + noise["spo2"]),
                "bpm": round(base["bpm"] + 4 * wave + noise["bpm"]),
                "weight": round(
                    base["weight"] + base["weight_trend"] * day + 0.2 * wave + noise["weight"], 1
                ),
            }
            values.update(profile["events"].get(day, {}))
            moment = (start + timedelta(days=day)).replace(hour=hour)
            rows.append(
                {
                    "ts": iso(moment),
                    "day": day,
                    "received": iso(received_at(profile, start, day, moment)),
                    **values,
                }
            )
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
            "received_at": row["received"],
        }
        if measurements_repository.put_measurement(item):
            patients_repository.touch_patient(code, item["ts"], DEVICE_ID)
            saved += 1
            label = profile.get("reviews", {}).get(row["day"])
            if label and item["alert"]:
                measurements_repository.set_review(
                    code,
                    item["ts"],
                    {
                        "status": label[0],
                        "note": label[1],
                        "reviewed_by": "demo@example.com",
                        "reviewed_at": iso(datetime.now(UTC)),
                    },
                )
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
