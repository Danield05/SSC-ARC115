/** Etiqueta de una alerta revisada (estilo PhysioTag). */
export type ReviewStatus = 'confirmada' | 'falso_positivo' | 'artefacto'

export interface Review {
  status: ReviewStatus
  /** Comentario de hasta 200 caracteres; puede ir vacío. */
  note: string
  /** Correo de quien la revisó. */
  reviewed_by: string
  /** ISO-8601 en UTC. */
  reviewed_at: string
}

export interface Measurement {
  record_id: string
  device_id: string
  /** ISO-8601 en UTC. */
  ts: string
  /** Cuándo la recibió el servidor (ISO-8601 en UTC); null en registros antiguos. */
  received_at: string | null
  weight_kg: number
  temp_c: number
  spo2: number
  bpm: number
  alert: boolean
  /** IMC calculado con el peso de esta medición; null si el paciente no tiene estatura. */
  bmi: number | null
  /** Categoría de la OMS según edad y sexo; null si no se puede clasificar. */
  bmi_category: string | null
  /** Revisión de la alerta; null si no se ha revisado (o si la medición no tiene alerta). */
  review: Review | null
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

/** Medición guardada que aún no tiene paciente (bandeja «Sin asignar»). */
export interface UnassignedMeasurement {
  record_id: string
  device_id: string
  device_name: string
  /** ISO-8601 en UTC. */
  ts: string
  received_at: string | null
  weight_kg: number
  temp_c: number
  spo2: number
  bpm: number
  alert: boolean
}

/** Resultado de asignar: `ts` de cada medición según lo que pasó con ella. */
export interface AssignResult {
  assigned: string[]
  /** El paciente ya tenía una medición con esa hora: se queda en la bandeja. */
  conflicts: string[]
  /** Ya asignada por otra persona, o de un dispositivo que este usuario no ve. */
  not_found: string[]
}

/** Estado de la orden «Medir a este paciente». */
export type OrderStatus = 'pendiente' | 'tomada' | 'completada' | 'cancelada' | 'expirada'

export interface MeasureOrder {
  command_id: string
  patient_code: string
  status: OrderStatus
  created_at: string
  expires_at: string
  taken_at: string | null
  completed_at: string | null
  /** Hora (ISO-8601 UTC) de la medición que cumplió la orden. */
  ts: string | null
}

/** Alertas de los últimos días que el rol puede ver (tarjeta del resumen). */
export interface AlertsSummary {
  days: number
  /** Mediciones del periodo, con paciente y sin asignar. */
  measurements: number
  alerts: number
  unassigned_alerts: number
  /** La alerta más reciente de un paciente, para enlazarla. */
  latest: { patient_code: string; ts: string } | null
}
