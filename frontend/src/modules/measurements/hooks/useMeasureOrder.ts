import { useEffect, useState } from 'react'
import * as api from '../api/measurementsApi'
import { notifyMeasurementReceived } from '../lib/events'
import type { MeasureOrder } from '../types'

const POLL_MS = 2000

/**
 * Orden «Medir a este paciente»: la crea y la consulta cada 2 s hasta que el aparato la cumple, o
 * hasta que el servidor la da por vencida (2 min sin que el aparato la tome; 5 min para medir).
 * Cuando llega la medición avisa a las pantallas del historial para que se actualicen.
 */
export function useMeasureOrder(deviceId: string, patientCode: string) {
  const [order, setOrder] = useState<MeasureOrder | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const commandId = order?.command_id
  const waiting = order?.status === 'pendiente' || order?.status === 'tomada'

  useEffect(() => {
    if (!commandId || !waiting) return
    let cancelled = false
    const timer = window.setInterval(async () => {
      try {
        const next = await api.fetchMeasureOrder(deviceId)
        if (cancelled) return
        // Otra persona dejó una orden nueva: la nuestra ya no cuenta.
        if (!next || next.command_id !== commandId) {
          setOrder((prev) => (prev ? { ...prev, status: 'cancelada' } : prev))
          return
        }
        setOrder(next)
        if (next.status === 'completada') notifyMeasurementReceived()
      } catch {
        // Un fallo de red momentáneo no corta la espera: se reintenta en el siguiente ciclo.
      }
    }, POLL_MS)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [commandId, waiting, deviceId])

  async function start() {
    setBusy(true)
    setError('')
    try {
      setOrder(await api.startMeasure(deviceId, patientCode))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo enviar la orden.')
    } finally {
      setBusy(false)
    }
  }

  async function cancel() {
    setBusy(true)
    try {
      const cancelled = await api.cancelMeasure(deviceId)
      if (cancelled) setOrder(cancelled)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cancelar.')
    } finally {
      setBusy(false)
    }
  }

  const reset = () => {
    setOrder(null)
    setError('')
  }

  return { order, error, busy, start, cancel, reset }
}
