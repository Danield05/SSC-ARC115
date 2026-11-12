import type { Measurement } from '../types'

/**
 * Hasta este retraso entre la medición y su recepción se considera enviada al momento: es la espera
 * máxima entre reintentos del firmware (SYNC_BACKOFF_MAX_MS, 5 minutos).
 */
export const ON_TIME_MS = 5 * 60 * 1000

export type SyncState = 'on_time' | 'offline' | 'unknown'

/** Milisegundos entre medir y llegar a la nube; null si el registro no trae la hora de recepción. */
export function delayMs(m: Measurement): number | null {
  if (!m.received_at) return null
  return Math.max(0, new Date(m.received_at).getTime() - new Date(m.ts).getTime())
}

export function syncState(m: Measurement): SyncState {
  const delay = delayMs(m)
  if (delay === null) return 'unknown'
  return delay <= ON_TIME_MS ? 'on_time' : 'offline'
}

/** «menos de 1 min», «35 min», «5 h», «2 d 17 h». */
export function formatDelay(ms: number): string {
  if (ms < 60_000) return 'menos de 1 min'
  const minutes = Math.round(ms / 60_000)
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return minutes % 60 ? `${hours} h ${minutes % 60} min` : `${hours} h`
  const days = Math.floor(hours / 24)
  return hours % 24 ? `${days} d ${hours % 24} h` : `${days} d`
}

/** Cuántas mediciones llegaron juntas: el servidor fija una sola hora de recepción por lote recibido. */
export function batchSizes(items: Measurement[]): Map<string, number> {
  const sizes = new Map<string, number>()
  for (const m of items) {
    if (m.received_at) sizes.set(m.received_at, (sizes.get(m.received_at) ?? 0) + 1)
  }
  return sizes
}
