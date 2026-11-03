"""Modelos de datos del módulo patients."""

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

PatientName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]

# Los campos opcionales aceptan "" para poder borrar un dato al editar.
Dui = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^(\d{8}-\d)?$")]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^([0-9+\-\s()]{7,20})?$")]
PatientEmail = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        max_length=254,
        pattern=r"^([^@\s]+@[^@\s]+\.[^@\s]+)?$",
    ),
]
Address = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
Age = Annotated[int, Field(ge=0, le=120)]
Sex = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[MF]$")]
HeightCm = Annotated[float, Field(ge=50, le=250)]


class PatientCreate(BaseModel):
    """El código lo asigna el sistema (P-0001, P-0002…). Nombre, edad y sexo son obligatorios."""

    name: PatientName
    age: Age
    sex: Sex
    dui: Dui | None = None
    email: PatientEmail | None = None
    phone: Phone | None = None
    address: Address | None = None
    height_cm: HeightCm | None = None


class PatientUpdate(BaseModel):
    """Solo se cambian los campos enviados; "" o null borran un dato opcional (no edad ni sexo)."""

    name: PatientName | None = None
    dui: Dui | None = None
    age: Age | None = None
    email: PatientEmail | None = None
    phone: Phone | None = None
    address: Address | None = None
    sex: Sex | None = None
    height_cm: HeightCm | None = None

    @model_validator(mode="after")
    def required_fields_stay(self):
        for field in ("name", "age", "sex"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} no se puede borrar")
        return self


class PatientOut(BaseModel):
    patient_code: str
    name: str = ""
    dui: str = ""
    age: int | None = None
    email: str = ""
    phone: str = ""
    address: str = ""
    sex: str = ""
    height_cm: float | None = None
    first_seen: str = ""
    last_seen: str = ""
    device_ids: list[str] = []
