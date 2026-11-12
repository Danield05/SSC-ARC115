import { useCallback, useEffect, useState } from 'react'
import * as api from '../api/measurementsApi'
import type { AssignResult, UnassignedMeasurement } from '../types'

/** Bandeja «Sin asignar»: las mediciones que llegaron sin paciente y cómo asignarlas. */
export function useUnassigned() {
  const [items, setItems] = useState<UnassignedMeasurement[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const reload = useCallback(async () => {
    try {
      setItems(await api.fetchUnassigned())
      setError('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al cargar las mediciones sin asignar.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    api
      .fetchUnassigned()
      .then((data) => {
        if (!cancelled) setItems(data)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Error al cargar las mediciones sin asignar.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  /** Asigna las mediciones elegidas y vuelve a pedir la bandeja. */
  const assign = async (patientCode: string, chosen: { device_id: string; ts: string }[]): Promise<AssignResult> => {
    const result = await api.assignUnassigned(patientCode, chosen)
    await reload()
    return result
  }

  return { items, loading, error, reload, assign }
}
