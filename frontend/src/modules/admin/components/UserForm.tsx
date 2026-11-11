import { useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ROLE_OPTIONS } from '../../auth/types'
import type { Role } from '../../auth/types'
import type { User } from '../../auth/types'
import type { NewUser } from '../types'

interface Props {
  /** Usuario que se edita; sin él, el formulario invita a uno nuevo. */
  editing?: User
  /** Quien edita su propia cuenta no puede cambiarse el rol. */
  isSelf?: boolean
  onCreate: (data: NewUser) => Promise<void>
  onUpdate: (email: string, changes: { name?: string; role?: Role }) => Promise<void>
  onDone: () => void
}

export default function UserForm({ editing, isSelf, onCreate, onUpdate, onDone }: Props) {
  const [email, setEmail] = useState(editing?.email ?? '')
  const [name, setName] = useState(editing?.name ?? '')
  const [role, setRole] = useState<Role>(editing?.role ?? 'promoter')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (editing) {
        await onUpdate(editing.email, { name: name.trim(), ...(!isSelf && { role }) })
      } else {
        await onCreate({ email: email.trim(), name: name.trim(), role })
      }
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el usuario.')
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
        <Input
          id="user-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={!!editing}
        />
      </div>
      <div className="space-y-2">
        <Label>Rol</Label>
        <Select
          items={ROLE_OPTIONS}
          value={role}
          onValueChange={(v) => v && setRole(v as Role)}
          disabled={isSelf}
        >
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
      {!editing && (
        <p className="text-muted-foreground text-xs">
          El sistema genera una contraseña provisional y la envía a ese correo. Al entrar por primera vez, la
          persona crea la suya; con eso queda verificado su correo.
        </p>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <Button type="submit" className="w-full" disabled={busy}>
        {busy ? 'Guardando…' : editing ? 'Guardar cambios' : 'Enviar invitación'}
      </Button>
    </form>
  )
}
