import { useState } from 'react'
import * as api from '../api/measurementsApi'
import type { ExportFormat } from '../api/measurementsApi'
import type { RangeDays } from '../types'

const DAY_MS = 24 * 60 * 60 * 1000

/** Descarga el historial del rango elegido y lo entrega al navegador como archivo. */
export function useExport(code: string, days: RangeDays, anonymize = false) {
  const [busy, setBusy] = useState<ExportFormat | null>(null)
  const [error, setError] = useState('')

  async function download(format: ExportFormat) {
    setBusy(format)
    setError('')
    try {
      const from = days ? new Date(Date.now() - days * DAY_MS).toISOString() : undefined
      const { blob, filename } = await api.downloadExport(code, format, from, anonymize)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo descargar el archivo.')
    } finally {
      setBusy(null)
    }
  }

  return { download, busy, error }
}
