import type { Measurement, Variable } from '../types'

/**
 * Desviación de cada medición frente a la línea base del propio paciente: sus 10 mediciones
 * anteriores. La idea (colorear según lo común que fue un valor en la ventana previa) viene de
 * Data Chromatix, de PhysioNet; solo se toma el método, no código. Es informativa: no es un
 * umbral clínico ni un diagnóstico.
 */
export const BASELINE_WINDOW = 10
/** Con menos mediciones anteriores no hay línea base y no se colorea. */
export const MIN_BASELINE = 3

/**
 * Desviación estándar mínima por variable. Si la serie es casi constante, un cambio mínimo daría
 * un z enorme y una falsa alarma; con este piso solo se marca lo que importa.
 */
export const MIN_STD: Record<Variable, number> = {
  temp_c: 0.1,
  spo2: 1,
  bpm: 2,
  weight_kg: 0.2,
}

export type DeviationLevel = 'normal' | 'attention' | 'deviation'

export interface Deviation {
  level: DeviationLevel
  /** (valor − promedio de la línea base) / desviación estándar (con el piso MIN_STD). */
  z: number
  direction: 'up' | 'down' | 'flat'
}

/** |z| < 1 normal; de 1 a 2 atención; 2 o más desvío. */
export function levelOf(z: number): DeviationLevel {
  const abs = Math.abs(z)
  if (abs >= 2) return 'deviation'
  if (abs >= 1) return 'attention'
  return 'normal'
}

/**
 * Desviación del valor `index` de la serie frente a las hasta 10 anteriores. `null` si hay menos
 * de MIN_BASELINE anteriores.
 */
export function deviationAt(values: number[], index: number, minStd: number): Deviation | null {
  const base = values.slice(Math.max(0, index - BASELINE_WINDOW), index)
  if (base.length < MIN_BASELINE) return null
  const mean = base.reduce((sum, v) => sum + v, 0) / base.length
  const variance = base.reduce((sum, v) => sum + (v - mean) ** 2, 0) / (base.length - 1)
  const std = Math.max(Math.sqrt(variance), minStd)
  const z = (values[index] - mean) / std
  return { level: levelOf(z), z, direction: z > 0 ? 'up' : z < 0 ? 'down' : 'flat' }
}

/** Desviaciones de toda la serie (de la más antigua a la más nueva) para una variable. */
export function deviationsOf(items: Measurement[], variable: Variable): (Deviation | null)[] {
  const values = items.map((m) => m[variable])
  return values.map((_, i) => deviationAt(values, i, MIN_STD[variable]))
}

/** Texto para quien no distingue colores y para lectores de pantalla. */
export function deviationLabel(d: Deviation | null): string {
  if (!d || d.level === 'normal') return ''
  const dir = d.direction === 'up' ? 'por encima' : 'por debajo'
  return d.level === 'deviation' ? `Desvío ${dir} de su línea base` : `Algo ${dir} de su línea base`
}

/** Fondo según el nivel: el color nunca va solo, siempre lo acompaña la flecha y el texto. */
export function deviationClass(d: Deviation | null | undefined): string {
  if (d?.level === 'deviation') return 'bg-destructive/15 text-destructive'
  if (d?.level === 'attention') return 'bg-warning/25 text-foreground'
  return ''
}
