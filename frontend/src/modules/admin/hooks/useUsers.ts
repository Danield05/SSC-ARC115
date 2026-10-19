import { useCallback, useEffect, useState } from 'react'
import type { User } from '../../auth/types'
import * as api from '../api/adminApi'
import type { NewUser } from '../types'

export function useUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const reload = useCallback(async () => {
    try {
      setUsers(await api.listUsers())
      setError('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al cargar los usuarios.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    api
      .listUsers()
      .then((data) => {
        if (!cancelled) setUsers(data)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Error al cargar los usuarios.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const create = async (data: NewUser) => {
    await api.createUser(data)
    await reload()
  }

  const setActive = async (email: string, active: boolean) => {
    await api.setUserActive(email, active)
    await reload()
  }

  return { users, loading, error, create, setActive }
}
