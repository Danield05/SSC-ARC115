export interface Patient {
  patient_code: string
  name: string
  dui: string
  /** Solo para menores de 18 años. */
  guardian_name: string
  guardian_dui: string
  age: number | null
  email: string
  phone: string
  address: string
  /** 'M', 'F' o vacío. */
  sex: string
  height_cm: number | null
  first_seen: string
  last_seen: string
  device_ids: string[]
}

/** Datos para registrar a un paciente: el código lo asigna el sistema. */
export interface NewPatient {
  name: string
  age: number
  sex: string
  dui?: string
  guardian_name?: string
  guardian_dui?: string
  email?: string
  phone?: string
  address?: string
  height_cm?: number
}

/** Cambios al editar: "" o null borran un dato opcional. */
export interface PatientChanges {
  name: string
  dui: string
  guardian_name: string
  guardian_dui: string
  /** La edad y el sexo no se pueden borrar. */
  age: number
  email: string
  phone: string
  address: string
  sex: string
  height_cm: number | null
}
