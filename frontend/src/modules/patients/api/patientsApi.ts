import { apiFetch, jsonBody } from '../../../shared/api/client'
import type { NewPatient, Patient } from '../types'

export const listPatients = () => apiFetch<Patient[]>('/patients')

export const createPatient = (data: NewPatient) =>
  apiFetch<Patient>('/patients', { method: 'POST', ...jsonBody(data) })

export const renamePatient = (code: string, name: string) =>
  apiFetch<Patient>(`/patients/${encodeURIComponent(code)}`, { method: 'PATCH', ...jsonBody({ name }) })
