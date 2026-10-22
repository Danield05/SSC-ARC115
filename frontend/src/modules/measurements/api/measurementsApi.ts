import { apiFetch } from '../../../shared/api/client'
import type { History } from '../types'

export const fetchHistory = (code: string, from?: string) => {
  const query = from ? `?from=${encodeURIComponent(from)}` : ''
  return apiFetch<History>(`/patients/${encodeURIComponent(code)}/measurements${query}`)
}
