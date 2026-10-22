export interface Patient {
  patient_code: string
  name: string
  dui: string
  age: number | null
  email: string
  phone: string
  address: string
  first_seen: string
  last_seen: string
  device_ids: string[]
}

/** Datos para registrar a un paciente: el código lo asigna el sistema. */
export interface NewPatient {
  name: string
  dui?: string
  age?: number
  email?: string
  phone?: string
  address?: string
}

/** Cambios al editar: "" o null borran un dato opcional. */
export interface PatientChanges {
  name: string
  dui: string
  age: number | null
  email: string
  phone: string
  address: string
}
