import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import PasswordInput from '@/shared/components/PasswordInput'
import AuthShell from '../components/AuthShell'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={user.must_change_password ? '/change-password' : '/dashboard'} replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const signedIn = await login(email, password)
      navigate(signedIn.must_change_password ? '/change-password' : '/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo iniciar sesión.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell
      splash
      title="Bienvenido"
      description="Ingresa para consultar el seguimiento de salud de tu comunidad."
      image="promotores-sonriendo.jpg"
      imageAlt="Dos promotores de salud sonriendo con gorras del Ministerio de Salud"
      quote="Medir a tiempo, registrar sin perder nada y avisar cuando algo se sale de lo normal."
    >
      <form onSubmit={onSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="email">Correo</Label>
          <Input
            id="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Contraseña</Label>
            <Link to="/forgot-password" className="text-primary text-xs hover:underline">
              ¿Olvidaste tu contraseña?
            </Link>
          </div>
          <PasswordInput
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? 'Entrando…' : 'Entrar'}
        </Button>
        <p className="text-muted-foreground text-center text-xs">
          ¿Aún no tienes acceso? Pídelo al equipo: te llegará una contraseña provisional por correo.
        </p>
      </form>
    </AuthShell>
  )
}
