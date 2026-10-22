import { useEffect, useState } from 'react'
import { getPatient } from '../api/patientsApi'
import type { Patient } from '../types'

/** Un paciente por código; `null` mientras carga o si no existe / no es visible para el rol. */
export function usePatient(code: string) {
  const [patient, setPatient] = useState<Patient | null>(null)

  useEffect(() => {
    let cancelled = false
    getPatient(code)
      .then((p) => {
        if (!cancelled) setPatient(p)
      })
      .catch(() => {
        if (!cancelled) setPatient(null)
      })
    return () => {
      cancelled = true
    }
  }, [code])

  return patient
}
