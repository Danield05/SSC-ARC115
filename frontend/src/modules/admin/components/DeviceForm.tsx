import { useState } from 'react'
import type { FormEvent } from 'react'
import type { NewDevice } from '../types'

interface Props {
  onCreate: (data: NewDevice) => Promise<void>
}

export default function DeviceForm({ onCreate }: Props) {
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
      setDeviceId('')
      setName('')
      setEmail('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar el dispositivo.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card grid" onSubmit={onSubmit}>
      <h2>Registrar dispositivo</h2>
      <label>
        Identificador
        <input value={deviceId} onChange={(e) => setDeviceId(e.target.value)} placeholder="ESP32-GP03-02" required />
      </label>
      <label>
        Nombre
        <input value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label>
        Correo del promotor
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={busy}>
        Registrar
      </button>
    </form>
  )
}
