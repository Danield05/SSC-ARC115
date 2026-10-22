import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import PasswordInput from '@/shared/components/PasswordInput'
import { changePassword } from '../api/authApi'
import AuthShell from '../components/AuthShell'
import { useAuth } from '../hooks/useAuth'

export default function ChangePasswordPage() {
  const { user, updateUser, logout } = useAuth()
  const navigate = useNavigate()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [repeat, setRepeat] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (!user) return <Navigate to="/login" replace />
  const forced = user.must_change_password

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (next !== repeat) {
      setError('Las contraseñas nuevas no coinciden.')
      return
    }
    setBusy(true)
    try {
      updateUser(await changePassword(current, next))
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cambiar la contraseña.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell
      title={forced ? 'Crea tu contraseña' : 'Cambia tu contraseña'}
      description={
        forced
          ? 'Entraste con una contraseña provisional. Crea la tuya para verificar tu cuenta y continuar.'
          : 'Escribe tu contraseña actual y la nueva.'
      }
      image="educacion-salud.jpg"
      imageAlt="Promotora de salud explicando un folleto a una joven en el corredor de su casa"
      quote="Tu contraseña protege los datos de las personas que cuidas."
    >
      <form onSubmit={onSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="current">{forced ? 'Contraseña provisional' : 'Contraseña actual'}</Label>
          <PasswordInput
            id="current"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="next">Contraseña nueva (mínimo 8 caracteres)</Label>
          <PasswordInput
            id="next"
            autoComplete="new-password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            minLength={8}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="repeat">Repite la contraseña nueva</Label>
          <PasswordInput
            id="repeat"
            autoComplete="new-password"
            value={repeat}
            onChange={(e) => setRepeat(e.target.value)}
            minLength={8}
            required
          />
        </div>
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? 'Guardando…' : 'Guardar contraseña'}
        </Button>
        <p className="text-center text-sm">
          {forced ? (
            <button type="button" onClick={logout} className="text-muted-foreground cursor-pointer hover:underline">
              Cerrar sesión
            </button>
          ) : (
            <Link to="/dashboard" className="text-primary hover:underline">
              Volver al panel
            </Link>
          )}
        </p>
      </form>
    </AuthShell>
  )
}
