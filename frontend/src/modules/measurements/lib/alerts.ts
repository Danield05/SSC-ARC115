import type { Measurement, Review, ReviewStatus, Thresholds } from '../types'
import { formatNumber, spo2OutOfRange, tempOutOfRange } from './format'

export const NOTE_MAX = 200

export const REVIEW_LABEL: Record<ReviewStatus, string> = {
  confirmada: 'Confirmada',
  falso_positivo: 'Falso positivo',
  artefacto: 'Artefacto',
}

/** Estilo del distintivo de cada etiqueta (el texto siempre acompaña al color). */
export const REVIEW_BADGE: Record<ReviewStatus, 'destructive' | 'secondary' | 'outline'> = {
  confirmada: 'destructive',
  falso_positivo: 'secondary',
  artefacto: 'outline',
}

export const REVIEW_HELP: Record<ReviewStatus, string> = {
  confirmada: 'La medición es real y la alerta era correcta.',
  falso_positivo: 'La medición es real, pero no había motivo de alerta.',
  artefacto: 'Lectura mala del sensor (mal contacto, movimiento).',
}

export const REVIEW_STATUSES = Object.keys(REVIEW_LABEL) as ReviewStatus[]

/** Por qué saltó la alerta, con los mismos umbrales que usa el servidor. */
export function reasons(m: Measurement, t: Thresholds): string[] {
  const out: string[] = []
  if (tempOutOfRange(m.temp_c, t)) {
    out.push(`Temperatura ${m.temp_c >= t.temp_high_c ? 'alta' : 'baja'} · ${formatNumber(m.temp_c, 1)} °C`)
  }
  if (spo2OutOfRange(m.spo2, t)) out.push(`SpO₂ baja · ${m.spo2} %`)
  return out
}

export interface Context {
  /** La medición anterior y la siguiente del historial; null si la alerta es la primera o la última del rango. */
  before: Measurement | null
  after: Measurement | null
  /** Las dos mediciones vecinas existen y están en rango: la alerta es una lectura suelta entre valores normales. */
  isolated: boolean
}

const inRange = (m: Measurement, t: Thresholds) => !tempOutOfRange(m.temp_c, t) && !spo2OutOfRange(m.spo2, t)

/** La medición anterior y la siguiente (del historial ordenado, de la más antigua a la más nueva). */
export function contextOf(items: Measurement[], index: number, t: Thresholds): Context {
  const before = index > 0 ? items[index - 1] : null
  const after = index < items.length - 1 ? items[index + 1] : null
  return { before, after, isolated: !!before && !!after && inRange(before, t) && inRange(after, t) }
}

export interface ReviewCounts {
  alerts: number
  reviewed: number
  confirmada: number
  falsePositive: number
  artifact: number
  /** Falsas alarmas (falso positivo + artefacto) entre las revisadas; null si aún no hay revisadas. */
  falseAlarmPct: number | null
}

export function countReviews(alerts: { review: Review | null }[]): ReviewCounts {
  const by = (s: ReviewStatus) => alerts.filter((a) => a.review?.status === s).length
  const confirmada = by('confirmada')
  const falsePositive = by('falso_positivo')
  const artifact = by('artefacto')
  const reviewed = confirmada + falsePositive + artifact
  return {
    alerts: alerts.length,
    reviewed,
    confirmada,
    falsePositive,
    artifact,
    falseAlarmPct: reviewed ? Math.round(((falsePositive + artifact) / reviewed) * 100) : null,
  }
}
