import { apiFetch, jsonBody } from '../../../shared/api/client'
import type { NewPatient, Patient, PatientChanges } from '../types'

export const listPatients = () => apiFetch<Patient[]>('/patients')

export const createPatient = (data: NewPatient) =>
  apiFetch<Patient>('/patients', { method: 'POST', ...jsonBody(data) })

export const updatePatient = (code: string, changes: PatientChanges) =>
  apiFetch<Patient>(`/patients/${encodeURIComponent(code)}`, { method: 'PATCH', ...jsonBody(changes) })
