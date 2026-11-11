import { useCallback, useEffect, useState } from 'react'
import * as api from '../api/adminApi'
import type { Device, NewDevice } from '../types'

export function useDevices() {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const reload = useCallback(async () => {
    try {
      setDevices(await api.listDevices())
      setError('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al cargar los dispositivos.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    api
      .listDevices()
      .then((data) => {
        if (!cancelled) setDevices(data)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Error al cargar los dispositivos.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const create = async (data: NewDevice) => {
    const created = await api.createDevice(data)
    await reload()
    return { id: created.device_id, key: created.api_key }
  }

  const setActive = async (id: string, active: boolean) => {
    await api.updateDevice(id, { active })
    await reload()
  }

  const update = async (id: string, changes: { name?: string; promoter_email?: string }) => {
    await api.updateDevice(id, changes)
    await reload()
  }

  const rotate = async (id: string) => (await api.rotateKey(id)).api_key

  return { devices, loading, error, create, update, setActive, rotate }
}
