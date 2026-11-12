"""Constantes compartidas entre módulos."""

# Las mediciones sin paciente (la bandeja «Sin asignar») se guardan en la tabla measurements con
# esta clave de partición seguida del dispositivo. El «#» no es válido en un código de paciente
# real, así que no puede chocar con uno, y separar por dispositivo evita que dos aparatos con la
# misma hora de medición se pisen como si fueran duplicados.
UNASSIGNED_CODE = "SIN-ASIGNAR"
UNASSIGNED_PREFIX = f"{UNASSIGNED_CODE}#"


def unassigned_key(device_id: str) -> str:
    return f"{UNASSIGNED_PREFIX}{device_id}"


def is_unassigned(patient_code: str) -> bool:
    return patient_code.startswith(UNASSIGNED_PREFIX)
