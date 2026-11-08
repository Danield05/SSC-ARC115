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
GuardianName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]
ADULT_AGE = 18


class PatientCreate(BaseModel):
    """El código lo asigna el sistema (P-0001, P-0002…). Nombre, edad y sexo son obligatorios."""

    name: PatientName
    age: Age
    sex: Sex
    dui: Dui | None = None
    guardian_name: GuardianName | None = None
    guardian_dui: Dui | None = None
    email: PatientEmail | None = None
    phone: Phone | None = None
    address: Address | None = None
    height_cm: HeightCm | None = None

    @model_validator(mode="after")
    def guardian_for_minors(self):
        """Un menor de 18 años no tiene DUI: se registra el de su responsable."""
        if self.age < ADULT_AGE:
            if not self.guardian_name or not self.guardian_dui:
                raise ValueError("Un menor de edad necesita nombre y DUI del responsable")
            self.dui = None
        else:
            self.guardian_name = None
            self.guardian_dui = None
        return self


class PatientUpdate(BaseModel):
    """Solo se cambian los campos enviados; "" o null borran un dato opcional (no edad ni sexo)."""

    name: PatientName | None = None
    dui: Dui | None = None
    guardian_name: GuardianName | None = None
    guardian_dui: Dui | None = None
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
        if self.age is not None and self.age < ADULT_AGE:
            if not self.guardian_name or not self.guardian_dui:
                raise ValueError("Un menor de edad necesita nombre y DUI del responsable")
            self.dui = ""
        elif self.age is not None:
            self.guardian_name = ""
            self.guardian_dui = ""
        return self


class PatientOut(BaseModel):
    patient_code: str
    name: str = ""
    dui: str = ""
    guardian_name: str = ""
    guardian_dui: str = ""
    age: int | None = None
    email: str = ""
    phone: str = ""
    address: str = ""
    sex: str = ""
    height_cm: float | None = None
    first_seen: str = ""
    last_seen: str = ""
    device_ids: list[str] = []
