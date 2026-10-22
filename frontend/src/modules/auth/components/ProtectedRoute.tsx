import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'
import PulseLoader from '@/shared/components/PulseLoader'
import { useAuth } from '../hooks/useAuth'
import type { Role } from '../types'

interface Props {
  roles?: Role[]
  children: ReactNode
}

export default function ProtectedRoute({ roles, children }: Props) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <PulseLoader />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  if (user.must_change_password) return <Navigate to="/change-password" replace />
  if (roles && !roles.includes(user.role)) {
    return (
      <div className="flex flex-col items-center gap-2 py-16 text-center">
        <ShieldAlert className="text-muted-foreground size-10" />
        <h1 className="text-lg font-semibold">Sin permiso</h1>
        <p className="text-muted-foreground text-sm">Tu rol no tiene acceso a esta sección.</p>
      </div>
    )
  }
  return <>{children}</>
}
