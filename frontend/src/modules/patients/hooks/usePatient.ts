import { useEffect, useState } from 'react'
import { getToken } from '@/shared/api/token'
import { getPatient } from '../api/patientsApi'
import type { Patient } from '../types'

// Último paciente leído por código: al pasar de una pestaña a otra el nombre aparece al instante
// mientras se vuelve a pedir. Se vacía al cambiar de sesión, para que otro usuario no vea lo que
// cargó el anterior.
const cache = new Map<string, Patient>()
let cacheOwner: string | null = null

function cached(code: string): Patient | null {
  const owner = getToken()
  if (owner !== cacheOwner) {
    cache.clear()
    cacheOwner = owner
  }
  return cache.get(code) ?? null
}

/**
 * Un paciente por código. `patient` es `null` mientras carga o si no existe / no es visible para
 * el rol; `loading` distingue ambos casos para no mostrar nada provisional mientras llega.
 */
export function usePatient(code: string) {
  const [loaded, setLoaded] = useState<{ code: string; patient: Patient | null } | null>(null)

  useEffect(() => {
    let cancelled = false
    getPatient(code)
      .then((p) => {
        if (cancelled) return
        cache.set(code, p)
        setLoaded({ code, patient: p })
      })
      .catch(() => {
        if (cancelled) return
        cache.delete(code)
        setLoaded({ code, patient: null })
      })
    return () => {
      cancelled = true
    }
  }, [code])

  const fresh = loaded?.code === code
  const patient = fresh ? loaded.patient : cached(code)
  return { patient, loading: !fresh && patient === null }
}
