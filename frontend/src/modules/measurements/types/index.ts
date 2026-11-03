export interface Measurement {
  record_id: string
  device_id: string
  /** ISO-8601 en UTC. */
  ts: string
  weight_kg: number
  temp_c: number
  spo2: number
  bpm: number
  alert: boolean
  /** IMC calculado con el peso de esta medición; null si el paciente no tiene estatura. */
  bmi: number | null
  /** Categoría de la OMS según edad y sexo; null si no se puede clasificar. */
  bmi_category: string | null
}

/** Umbrales de alerta del servidor; el frontend solo los dibuja. */
export interface Thresholds {
  temp_low_c: number
  temp_high_c: number
  spo2_min: number
}

export interface History {
  patient_code: string
  thresholds: Thresholds
  height_cm: number | null
  sex: string
  age: number | null
  items: Measurement[]
}

export interface Stats {
  avg: number
  min: number
  max: number
}

export interface SummaryWindow {
  n: number
  weight_kg: Stats | null
  temp_c: Stats | null
  spo2: Stats | null
  bpm: Stats | null
}

export type Variable = 'weight_kg' | 'temp_c' | 'spo2' | 'bpm'

export interface Trend {
  per_day: number
  label: 'sube' | 'baja' | 'estable'
}

/** Resumen del paciente; sin mediciones `count` es 0 y lo demás es null. */
export interface Summary {
  patient_code: string
  count: number
  first_ts: string | null
  last_ts: string | null
  latest: { ts: string; weight_kg: number; temp_c: number; spo2: number; bpm: number } | null
  bmi: { value: number; category: string | null; height_cm: number } | null
  weight_change: { vs_first_kg: number | null; vs_first_pct: number | null; vs_previous_kg: number | null } | null
  windows: Record<'7' | '30' | '90', SummaryWindow> | null
  trend: Record<Variable, Trend | null> | null
  alert_pct: number | null
  correlation: { temp_bpm: { r: number; n: number } | null } | null
}

/** Días hacia atrás desde hoy; `null` es todo el historial. */
export type RangeDays = 7 | 30 | 90 | null
