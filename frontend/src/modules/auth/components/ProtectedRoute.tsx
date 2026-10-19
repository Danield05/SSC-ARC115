import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import type { Role } from '../types'

interface Props {
  roles?: Role[]
  children: ReactNode
}

export default function ProtectedRoute({ roles, children }: Props) {
  const { user, loading } = useAuth()
  if (loading) return <p className="center">Cargando…</p>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) {
    return <p className="center">No tienes permiso para ver esta sección.</p>
  }
  return <>{children}</>
}
