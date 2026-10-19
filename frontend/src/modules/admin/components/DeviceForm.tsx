import { useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { NewDevice } from '../types'

interface Props {
  onCreate: (data: NewDevice) => Promise<void>
  onDone: () => void
}

export default function DeviceForm({ onCreate, onDone }: Props) {
  const [deviceId, setDeviceId] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onCreate({ device_id: deviceId.trim(), name: name.trim(), promoter_email: email })
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar el dispositivo.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="device-id">Identificador</Label>
        <Input
          id="device-id"
          value={deviceId}
          onChange={(e) => setDeviceId(e.target.value)}
          placeholder="ESP32-GP03-02"
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="device-name">Nombre</Label>
        <Input id="device-name" value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div className="space-y-2">
        <Label htmlFor="device-email">Correo del promotor</Label>
        <Input id="device-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <Button type="submit" className="w-full" disabled={busy}>
        {busy ? 'Registrando…' : 'Registrar'}
      </Button>
    </form>
  )
}
