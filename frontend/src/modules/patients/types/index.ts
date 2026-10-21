export interface Patient {
  patient_code: string
  name: string
  first_seen: string
  last_seen: string
  device_ids: string[]
}

export interface NewPatient {
  patient_code: string
  name: string
}
