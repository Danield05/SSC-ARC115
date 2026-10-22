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
  items: Measurement[]
}

/** Días hacia atrás desde hoy; `null` es todo el historial. */
export type RangeDays = 7 | 30 | 90 | null
