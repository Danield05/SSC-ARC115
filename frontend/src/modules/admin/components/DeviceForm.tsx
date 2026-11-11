import { useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { Device, NewDevice } from '../types'

interface Props {
  /** Dispositivo que se edita; sin él, el formulario registra uno nuevo. */
  editing?: Device
  onCreate: (data: NewDevice) => Promise<void>
  onUpdate: (id: string, changes: NewDevice) => Promise<void>
  onDone: () => void
}

export default function DeviceForm({ editing, onCreate, onUpdate, onDone }: Props) {
  const [name, setName] = useState(editing?.name ?? '')
  const [email, setEmail] = useState(editing?.promoter_email ?? '')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const data = { name: name.trim(), promoter_email: email.trim() }
      if (editing) await onUpdate(editing.device_id, data)
      else await onCreate(data)
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el dispositivo.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="device-name">Nombre</Label>
        <Input
          id="device-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Equipo de la unidad de salud"
          maxLength={100}
          required
          autoFocus
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="device-email">Correo del promotor</Label>
        <Input id="device-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <p className="text-muted-foreground text-xs">
          Recibirá un correo con las alertas cada vez que el dispositivo sincronice.
        </p>
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <Button type="submit" className="w-full" disabled={busy}>
        {busy ? 'Guardando…' : editing ? 'Guardar cambios' : 'Registrar'}
      </Button>
    </form>
  )
}
