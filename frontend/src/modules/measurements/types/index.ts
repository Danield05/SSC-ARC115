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

/** Días hacia atrás desde hoy; `null` es todo el historial. */
export type RangeDays = 7 | 30 | 90 | null
