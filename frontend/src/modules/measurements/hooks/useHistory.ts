import { useEffect, useState } from 'react'
import { ApiError } from '../../../shared/api/client'
import * as api from '../api/measurementsApi'
import { onMeasurementReceived } from '../lib/events'
import type { History, RangeDays } from '../types'

const DAY_MS = 24 * 60 * 60 * 1000

/**
 * Historial de un paciente en el rango elegido. Mientras llega un rango nuevo se conserva el
 * anterior (`loading` en verdadero) para que las gráficas no parpadeen ni salten.
 */
export function useHistory(code: string, days: RangeDays) {
  const [data, setData] = useState<History | null>(null)
  const [error, setError] = useState('')
  const [notFound, setNotFound] = useState(false)
  // Última consulta terminada; `loading` es que la consulta actual aún no terminó.
  const [doneKey, setDoneKey] = useState('')
  // Sube cada vez que llega una medición nueva (orden «Medir» completada) para pedir los datos otra vez.
  const [reloads, setReloads] = useState(0)
  const key = `${code}|${days}|${reloads}`

  useEffect(() => onMeasurementReceived(() => setReloads((n) => n + 1)), [])

  useEffect(() => {
    let cancelled = false
    const from = days ? new Date(Date.now() - days * DAY_MS).toISOString() : undefined
    api
      .fetchHistory(code, from)
      .then((history) => {
        if (cancelled) return
        setData(history)
        setError('')
        setNotFound(false)
      })
      .catch((e) => {
        if (cancelled) return
        if (e instanceof ApiError && e.status === 404) setNotFound(true)
        else setError(e instanceof Error ? e.message : 'Error al cargar el historial.')
      })
      .finally(() => {
        if (!cancelled) setDoneKey(key)
      })
    return () => {
      cancelled = true
    }
  }, [code, days, key])

  return {
    // Nunca se muestran datos de otro paciente mientras llegan los del actual.
    data: data?.patient_code === code ? data : null,
    loading: doneKey !== key,
    error,
    notFound,
  }
}
