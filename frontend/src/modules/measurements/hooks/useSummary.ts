import { useEffect, useState } from 'react'
import * as api from '../api/measurementsApi'
import { onMeasurementReceived } from '../lib/events'
import type { Summary } from '../types'

/** Resumen de un paciente (todo su historial, no depende del rango elegido). */
export function useSummary(code: string) {
  const [data, setData] = useState<Summary | null>(null)
  const [error, setError] = useState('')
  const [reloads, setReloads] = useState(0)

  useEffect(() => onMeasurementReceived(() => setReloads((n) => n + 1)), [])

  useEffect(() => {
    let cancelled = false
    api
      .fetchSummary(code)
      .then((summary) => {
        if (cancelled) return
        setData(summary)
        setError('')
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Error al cargar el resumen.')
      })
    return () => {
      cancelled = true
    }
  }, [code, reloads])

  // Nunca se muestran datos de otro paciente mientras llegan los del actual.
  return { data: data?.patient_code === code ? data : null, error }
}
