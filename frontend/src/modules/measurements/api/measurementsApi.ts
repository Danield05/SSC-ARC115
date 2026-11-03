import { apiDownload, apiFetch } from '../../../shared/api/client'
import type { History, Summary } from '../types'

export const fetchHistory = (code: string, from?: string) => {
  const query = from ? `?from=${encodeURIComponent(from)}` : ''
  return apiFetch<History>(`/patients/${encodeURIComponent(code)}/measurements${query}`)
}

export const fetchSummary = (code: string) =>
  apiFetch<Summary>(`/patients/${encodeURIComponent(code)}/summary`)

export type ExportFormat = 'xlsx' | 'csv'

/** Archivo del historial (Excel o CSV) del rango elegido; anonimizado: solo el código del paciente. */
export const downloadExport = (code: string, format: ExportFormat, from?: string) => {
  const params = new URLSearchParams({ format })
  if (from) params.set('from', from)
  return apiDownload(`/patients/${encodeURIComponent(code)}/export?${params}`)
}
