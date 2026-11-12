import type { UnassignedMeasurement } from '../types'

/** Dos mediciones del mismo dispositivo con menos de esto de diferencia son de la misma visita. */
export const VISIT_GAP_MS = 15 * 60 * 1000

export interface Visit {
  /** Estable entre recargas: dispositivo y hora de la primera medición. */
  key: string
  device_id: string
  device_name: string
  /** De la más nueva a la más antigua, como llegan del servidor. */
  items: UnassignedMeasurement[]
}

/** Clave única de una medición de la bandeja (el servidor la identifica por dispositivo y hora). */
export const itemKey = (m: Pick<UnassignedMeasurement, 'device_id' | 'ts'>) => `${m.device_id}|${m.ts}`

/**
 * Agrupa las mediciones por visita: las del mismo dispositivo que van seguidas (sin un hueco de más
 * de VISIT_GAP_MS) se asignan juntas con un clic. Devuelve las visitas de la más reciente a la más
 * antigua.
 */
export function groupVisits(items: UnassignedMeasurement[]): Visit[] {
  const byDevice = new Map<string, UnassignedMeasurement[]>()
  for (const m of items) byDevice.set(m.device_id, [...(byDevice.get(m.device_id) ?? []), m])

  const visits: Visit[] = []
  for (const [device_id, list] of byDevice) {
    const ordered = [...list].sort((a, b) => Date.parse(a.ts) - Date.parse(b.ts))
    let current: UnassignedMeasurement[] = []
    const close = () => {
      if (current.length === 0) return
      visits.push({
        key: `${device_id}|${current[0].ts}`,
        device_id,
        device_name: current[0].device_name,
        items: [...current].reverse(),
      })
      current = []
    }
    for (const m of ordered) {
      const last = current[current.length - 1]
      if (last && Date.parse(m.ts) - Date.parse(last.ts) > VISIT_GAP_MS) close()
      current.push(m)
    }
    close()
  }
  return visits.sort((a, b) => Date.parse(b.items[0].ts) - Date.parse(a.items[0].ts))
}
