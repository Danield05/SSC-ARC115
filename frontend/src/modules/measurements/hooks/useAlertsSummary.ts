import { useEffect, useState } from 'react'
import * as api from '../api/measurementsApi'
import type { AlertsSummary } from '../types'

/** Alertas recientes para la tarjeta del resumen. `null` mientras carga o si falla. */
export function useAlertsSummary() {
  const [data, setData] = useState<AlertsSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    api
      .fetchAlertsSummary()
      .then((summary) => {
        if (!cancelled) setData(summary)
      })
      .catch(() => {
        // La tarjeta es informativa: si falla se queda en «—» sin romper el resumen.
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { data, loading }
}
