import { getToken } from './token'

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function messageFrom(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return 'Revisa los datos: hay campos con formato inválido.'
  return fallback
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body) headers.set('Content-Type', 'application/json')

  let res: Response
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor.')
  }
  const body: unknown = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, messageFrom(body, `Error ${res.status}`))
  return body as T
}

/** Descarga un archivo (por ejemplo, un Excel): devuelve el contenido y el nombre que manda el servidor. */
export async function apiDownload(path: string): Promise<{ blob: Blob; filename: string }> {
  const headers = new Headers()
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let res: Response
  try {
    res = await fetch(`${API_URL}${path}`, { headers })
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor.')
  }
  if (!res.ok) {
    const body: unknown = await res.json().catch(() => null)
    throw new ApiError(res.status, messageFrom(body, `Error ${res.status}`))
  }
  const disposition = res.headers.get('Content-Disposition') ?? ''
  const filename = /filename="?([^";]+)"?/.exec(disposition)?.[1] ?? 'exportacion'
  return { blob: await res.blob(), filename }
}

export function jsonBody(data: unknown): RequestInit {
  return { body: JSON.stringify(data) }
}
