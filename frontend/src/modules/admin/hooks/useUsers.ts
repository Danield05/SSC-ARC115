import { useCallback, useEffect, useState } from 'react'
import type { Role, User } from '../../auth/types'
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
    await api.updateUser(email, { active })
    await reload()
  }

  const setRole = async (email: string, role: Role) => {
    await api.updateUser(email, { role })
    await reload()
  }

  const update = async (email: string, changes: { name?: string; role?: Role }) => {
    await api.updateUser(email, changes)
    await reload()
  }

  const resend = async (email: string) => {
    await api.resendInvite(email)
  }

  return { users, loading, error, create, update, setActive, setRole, resend }
}
