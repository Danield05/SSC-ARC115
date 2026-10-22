import { useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ROLE_OPTIONS } from '../../auth/types'
import type { Role } from '../../auth/types'
import type { NewUser } from '../types'

interface Props {
  onCreate: (data: NewUser) => Promise<void>
  onDone: () => void
}

export default function UserForm({ onCreate, onDone }: Props) {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState<Role>('promoter')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onCreate({ email: email.trim(), name: name.trim(), role })
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el usuario.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="user-name">Nombre</Label>
        <Input id="user-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} autoFocus />
      </div>
      <div className="space-y-2">
        <Label htmlFor="user-email">Correo</Label>
        <Input id="user-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label>Rol</Label>
        <Select items={ROLE_OPTIONS} value={role} onValueChange={(v) => v && setRole(v as Role)}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ROLE_OPTIONS.map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <p className="text-muted-foreground text-xs">
        El sistema genera una contraseña provisional y la envía a ese correo. Al entrar por primera vez, la
        persona crea la suya; con eso queda verificado su correo.
      </p>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <Button type="submit" className="w-full" disabled={busy}>
        {busy ? 'Enviando invitación…' : 'Enviar invitación'}
      </Button>
    </form>
  )
}
