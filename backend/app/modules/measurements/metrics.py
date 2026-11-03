"""Métricas del paciente (promedios, tendencia, correlación). Funciones puras, sin AWS.

Todas reciben mediciones como diccionarios con `ts` (ISO-8601 UTC, "...Z") y los valores
`weight_kg`, `temp_c`, `spo2`, `bpm`, `alert`, de la más antigua a la más nueva. Son informativas:
el sistema no emite diagnósticos.
"""

import math
from datetime import datetime, timedelta

VARIABLES = ("weight_kg", "temp_c", "spo2", "bpm")
WINDOW_DAYS = (7, 30, 90)
MIN_CORRELATION_PAIRS = 10

# Cambio por día por debajo del cual la serie se considera estable.
TREND_TOLERANCE_PER_DAY = {"weight_kg": 0.02, "temp_c": 0.02, "spo2": 0.05, "bpm": 0.2}


def parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def window(items: list[dict], days: int) -> list[dict]:
    """Mediciones con `ts >= última - days`. La ventana termina en la última medición, no en hoy."""
    if not items:
        return []
    start = parse_ts(items[-1]["ts"]) - timedelta(days=days)
    return [m for m in items if parse_ts(m["ts"]) >= start]


def stats(values: list[float]) -> dict | None:
    """Promedio, mínimo y máximo; None si no hay valores."""
    if not values:
        return None
    values = [float(v) for v in values]
    return {
        "avg": round(sum(values) / len(values), 2),
        "min": min(values),
        "max": max(values),
    }


def slope_per_day(points: list[tuple[datetime, float]]) -> float | None:
    """Pendiente de la regresión lineal (unidad por día). None con menos de 2 puntos o sin
    variación en el tiempo."""
    if len(points) < 2:
        return None
    t0 = points[0][0]
    xs = [(t - t0).total_seconds() / 86400 for t, _ in points]
    ys = [float(v) for _, v in points]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    var_x = sum((x - mean_x) ** 2 for x in xs)
    if var_x == 0:
        return None
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / var_x


def trend_label(variable: str, per_day: float | None) -> str | None:
    """`sube`, `baja` o `estable` según la tolerancia de la variable."""
    if per_day is None:
        return None
    tolerance = TREND_TOLERANCE_PER_DAY[variable]
    if per_day > tolerance:
        return "sube"
    if per_day < -tolerance:
        return "baja"
    return "estable"


def pearson(xs: list[float], ys: list[float]) -> float | None:
    """Coeficiente de correlación de Pearson. None con menos de 10 pares o varianza cero."""
    n = len(xs)
    if n != len(ys) or n < MIN_CORRELATION_PAIRS:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    syy = sum((y - mean_y) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    return max(-1.0, min(1.0, sxy / math.sqrt(sxx * syy)))


def alert_percentage(items: list[dict]) -> float | None:
    if not items:
        return None
    return round(100 * sum(1 for m in items if m.get("alert")) / len(items), 1)


def weight_change(items: list[dict]) -> dict | None:
    """Variación del último peso contra el primero y contra el anterior."""
    if not items:
        return None
    last = float(items[-1]["weight_kg"])
    first = float(items[0]["weight_kg"])
    vs_first_pct = round(100 * (last - first) / first, 1) if len(items) > 1 and first else None
    return {
        "vs_first_kg": round(last - first, 1) if len(items) > 1 else None,
        "vs_first_pct": vs_first_pct,
        "vs_previous_kg": round(last - float(items[-2]["weight_kg"]), 1)
        if len(items) > 1
        else None,
    }
