import { MailCheck } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button, buttonVariants } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { forgotPassword } from '../api/authApi'
import AuthShell from '../components/AuthShell'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [sentTo, setSentTo] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await forgotPassword(email.trim())
      setSentTo(email.trim())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo enviar la solicitud.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell
      title="Recupera tu contraseña"
      description="Escribe tu correo y te enviaremos una contraseña provisional."
      image="visita-rural.jpg"
      imageAlt="Promotor de salud con una tablilla conversando con una vecina frente a su casa"
      quote="Si la olvidaste, no pasa nada: en un minuto vuelves a entrar."
    >
      {sentTo ? (
        <div className="space-y-5">
          <Alert>
            <MailCheck />
            <AlertTitle>Revisa tu correo</AlertTitle>
            <AlertDescription>
              Si <strong>{sentTo}</strong> está registrado, te enviamos una contraseña provisional. Es válida por
              30 minutos; al entrar con ella te pediremos crear una nueva. Revisa también la carpeta de spam.
            </AlertDescription>
          </Alert>
          <Link to="/login" className={buttonVariants({ className: 'w-full' })}>
            Ir a iniciar sesión
          </Link>
        </div>
      ) : (
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
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? 'Enviando…' : 'Enviar contraseña provisional'}
          </Button>
          <p className="text-center text-sm">
            <Link to="/login" className="text-primary hover:underline">
              Volver a iniciar sesión
            </Link>
          </p>
        </form>
      )}
    </AuthShell>
  )
}
