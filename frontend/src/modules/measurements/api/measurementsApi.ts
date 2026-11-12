import { apiDownload, apiFetch, jsonBody } from '../../../shared/api/client'
import type { AlertsSummary, AssignResult, History, MeasureOrder, Review, ReviewStatus, Summary, UnassignedMeasurement } from '../types'

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

/** Mediciones sin paciente de los dispositivos del usuario (la bandeja «Sin asignar»). */
export const fetchUnassigned = () => apiFetch<UnassignedMeasurement[]>('/measurements/unassigned')

/** Mueve mediciones de la bandeja a un paciente; solo admin y promotor. */
export const assignUnassigned = (patientCode: string, items: { device_id: string; ts: string }[]) =>
  apiFetch<AssignResult>('/measurements/unassigned/assign', {
    method: 'POST',
    ...jsonBody({ patient_code: patientCode, items }),
  })

const measurePath = (deviceId: string) => `/devices/${encodeURIComponent(deviceId)}/measure`

/** «Medir a este paciente»: deja la orden para que el aparato la tome. */
export const startMeasure = (deviceId: string, patientCode: string) =>
  apiFetch<MeasureOrder>(measurePath(deviceId), { method: 'POST', ...jsonBody({ patient_code: patientCode }) })

/** Última orden del dispositivo y su estado; null si nunca hubo una. */
export const fetchMeasureOrder = (deviceId: string) => apiFetch<MeasureOrder | null>(measurePath(deviceId))

export const cancelMeasure = (deviceId: string) =>
  apiFetch<MeasureOrder | null>(measurePath(deviceId), { method: 'DELETE' })

/** Alertas de los últimos 7 días que el rol puede ver. */
export const fetchAlertsSummary = () => apiFetch<AlertsSummary>('/measurements/alerts-summary')
