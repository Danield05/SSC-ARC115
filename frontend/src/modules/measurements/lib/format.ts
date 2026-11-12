import type { Thresholds } from '../types'

export const formatDateTime = (iso: string) =>
  new Date(iso).toLocaleString('es-SV', { dateStyle: 'medium', timeStyle: 'short' })

export const formatDate = (iso: string) => new Date(iso).toLocaleDateString('es-SV', { dateStyle: 'medium' })

export const formatNumber = (value: number, decimals: number) =>
  value.toLocaleString('es-SV', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })

/** Misma regla que el servidor: temperatura ≤ mínimo o ≥ máximo. */
export const tempOutOfRange = (value: number, t: Thresholds) => value <= t.temp_low_c || value >= t.temp_high_c

/** Misma regla que el servidor: SpO₂ por debajo del mínimo. */
export const spo2OutOfRange = (value: number, t: Thresholds) => value < t.spo2_min

export interface Band {
  from: number
  to: number
}

/**
 * Límites del eje Y con aire alrededor de los datos. Si hay una franja de rango normal, se
 * incluye completa para que siempre se vea.
 */
export function paddedDomain(values: number[], band?: Band, ceiling?: number): [number, number] {
  const all = band ? [...values, band.from, band.to] : values
  if (all.length === 0) return [0, 1]
  const min = Math.min(...all)
  const max = Math.max(...all)
  const pad = Math.max((max - min) * 0.15, 0.5)
  const hi = ceiling !== undefined ? Math.min(max + pad, ceiling) : max + pad
  return [Math.floor(min - pad), Math.ceil(hi)]
}
