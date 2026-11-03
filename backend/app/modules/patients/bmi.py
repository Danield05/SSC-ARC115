"""Índice de masa corporal (IMC) y su categoría de la OMS. Funciones puras, sin AWS.

Adultos (18 años o más): cortes fijos de la OMS. De 5 a 17 años: puntuaciones z de la referencia
de crecimiento de la OMS por edad y sexo (`who_bmi.py`). Menores de 5 años no tienen categoría
(la OMS usa peso para la talla, que aquí no se mide).
"""

from app.modules.patients.who_bmi import CUTOFFS

ADULT_AGE = 18

# (límite superior exclusivo, categoría) en orden creciente.
_CATEGORIES = (
    (18.5, "Bajo peso"),
    (25.0, "Normal"),
    (30.0, "Sobrepeso"),
    (35.0, "Obesidad grado I"),
    (40.0, "Obesidad grado II"),
)


def bmi(weight_kg: float, height_cm: float | None) -> float | None:
    """kg / m², con un decimal. None si falta la estatura."""
    if not height_cm or height_cm <= 0:
        return None
    meters = float(height_cm) / 100
    return round(float(weight_kg) / (meters * meters), 1)


def bmi_category(value: float | None, age: int | None, sex: str | None = None) -> str | None:
    """Categoría del IMC según la edad (y el sexo en menores). None si no se puede clasificar."""
    if value is None or age is None:
        return None
    if age >= ADULT_AGE:
        for limit, label in _CATEGORIES:
            if value < limit:
                return label
        return "Obesidad grado III"
    cutoffs = CUTOFFS.get(sex or "", {}).get(age)
    if cutoffs is None:
        return None
    z3, z2, z_plus1, z_plus2 = cutoffs
    if value < z3:
        return "Delgadez severa"
    if value < z2:
        return "Delgadez"
    if value <= z_plus1:
        return "Normal"
    if value <= z_plus2:
        return "Sobrepeso"
    return "Obesidad"
