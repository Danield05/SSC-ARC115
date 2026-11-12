import { apiDownload, apiFetch, jsonBody } from '../../../shared/api/client'
import type { History, Review, ReviewStatus, Summary } from '../types'

export const fetchHistory = (code: string, from?: string) => {
  const query = from ? `?from=${encodeURIComponent(from)}` : ''
  return apiFetch<History>(`/patients/${encodeURIComponent(code)}/measurements${query}`)
}

export const fetchSummary = (code: string) =>
  apiFetch<Summary>(`/patients/${encodeURIComponent(code)}/summary`)

/** Etiqueta una alerta; solo admin y promotor (el evaluador recibe 403). Reemplaza la revisión anterior. */
export const reviewAlert = (code: string, ts: string, review: { status: ReviewStatus; note: string }) =>
  apiFetch<Review>(
    `/patients/${encodeURIComponent(code)}/measurements/${encodeURIComponent(ts)}/review`,
    { method: 'PATCH', ...jsonBody(review) },
  )

export type ExportFormat = 'xlsx' | 'csv'

/**
 * Archivo del historial (Excel o CSV) del rango elegido. Sin nombre ni contactos; con `anonymize`
 * además lleva un ID sustituto en lugar del código y los días desde la primera medición en lugar
 * de las fechas.
 */
export const downloadExport = (code: string, format: ExportFormat, from?: string, anonymize = false) => {
  const params = new URLSearchParams({ format })
  if (from) params.set('from', from)
  if (anonymize) params.set('anonymize', 'true')
  return apiDownload(`/patients/${encodeURIComponent(code)}/export?${params}`)
}
