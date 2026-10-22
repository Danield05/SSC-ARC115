import { useCallback, useEffect, useState } from 'react'
import * as api from '../api/patientsApi'
import type { NewPatient, Patient, PatientChanges } from '../types'

export function usePatients() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const reload = useCallback(async () => {
    try {
      setPatients(await api.listPatients())
      setError('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al cargar los pacientes.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    api
      .listPatients()
      .then((data) => {
        if (!cancelled) setPatients(data)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Error al cargar los pacientes.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const create = async (data: NewPatient) => {
    const created = await api.createPatient(data)
    await reload()
    return created
  }

  const update = async (code: string, changes: PatientChanges) => {
    await api.updatePatient(code, changes)
    await reload()
  }

  return { patients, loading, error, create, update }
}
