import type { Measurement, ReviewStatus, Thresholds } from '../types'
import { formatNumber, spo2OutOfRange, tempOutOfRange } from './format'
import { formatDelay } from './traceability'

/** Alertas seguidas (sin una medición normal en medio) que se leen como un solo episodio. */
export interface Episode {
  /** Las mediciones con alerta del episodio, de la más antigua a la más nueva. */
  alerts: Measurement[]
  start: string
  end: string
  /** La primera medición sin alerta después del episodio; null si no la hay en el rango. */
  recovery: Measurement | null
}

/**
 * Agrupa las alertas consecutivas del historial (de la más antigua a la más nueva). Una alerta
 * sola es un episodio de una medición. Es solo una forma de leer los datos, no un diagnóstico.
 */
export function findEpisodes(items: Measurement[]): Episode[] {
  const episodes: Episode[] = []
  let run: Measurement[] = []
  items.forEach((m, i) => {
    if (m.alert) run.push(m)
    if (run.length > 0 && (!m.alert || i === items.length - 1)) {
      episodes.push({ alerts: run, start: run[0].ts, end: run[run.length - 1].ts, recovery: m.alert ? null : m })
      run = []
    }
  })
  return episodes
}

/** Tiempo entre la primera y la última alerta del episodio. */
export function spanText(ep: Episode): string {
  const ms = new Date(ep.end).getTime() - new Date(ep.start).getTime()
  return ms <= 0 ? 'Una sola medición' : formatDelay(ms)
}

/** Los valores más extremos de lo que disparó la alerta, con la unidad. */
export function extremes(ep: Episode, t: Thresholds): string[] {
  const out: string[] = []
  const highTemps = ep.alerts.filter((m) => m.temp_c >= t.temp_high_c).map((m) => m.temp_c)
  const lowTemps = ep.alerts.filter((m) => m.temp_c <= t.temp_low_c).map((m) => m.temp_c)
  const lowSpo2 = ep.alerts.filter((m) => spo2OutOfRange(m.spo2, t)).map((m) => m.spo2)
  if (highTemps.length) out.push(`Temperatura más alta: ${formatNumber(Math.max(...highTemps), 1)} °C`)
  if (lowTemps.length) out.push(`Temperatura más baja: ${formatNumber(Math.min(...lowTemps), 1)} °C`)
  if (lowSpo2.length) out.push(`SpO₂ más baja: ${Math.min(...lowSpo2)} %`)
  // Alerta marcada por el dispositivo sin pasar los umbrales del servidor.
  if (!out.length && ep.alerts.some((m) => !tempOutOfRange(m.temp_c, t) && !spo2OutOfRange(m.spo2, t))) {
    out.push('Marcada por el dispositivo')
  }
  return out
}

export type EpisodeReview =
  | { kind: 'pending'; total: number }
  | { kind: 'partial'; reviewed: number; total: number }
  | { kind: 'done'; total: number; statuses: ReviewStatus[] }

/** Cuántas alertas del episodio ya tienen etiqueta y cuáles. */
export function reviewOf(ep: Episode): EpisodeReview {
  const total = ep.alerts.length
  const statuses = ep.alerts.flatMap((m) => (m.review ? [m.review.status] : []))
  if (statuses.length === 0) return { kind: 'pending', total }
  if (statuses.length < total) return { kind: 'partial', reviewed: statuses.length, total }
  return { kind: 'done', total, statuses: [...new Set(statuses)] }
}

/** Cómo se dibuja el episodio en la línea de tiempo: lo pendiente manda sobre lo revisado. */
export type EpisodeMark = 'pending' | ReviewStatus

export function markOf(ep: Episode): EpisodeMark {
  const r = reviewOf(ep)
  if (r.kind !== 'done') return 'pending'
  if (r.statuses.includes('confirmada')) return 'confirmada'
  if (r.statuses.includes('falso_positivo')) return 'falso_positivo'
  return 'artefacto'
}
