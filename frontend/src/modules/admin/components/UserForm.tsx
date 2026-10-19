import { useState } from 'react'
import type { FormEvent } from 'react'
import { ROLE_LABELS } from '../../auth/types'
import type { Role } from '../../auth/types'
import type { NewUser } from '../types'

interface Props {
  onCreate: (data: NewUser) => Promise<void>
}

export default function UserForm({ onCreate }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<Role>('promoter')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onCreate({ email, password, role })
      setEmail('')
      setPassword('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear el usuario.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card grid" onSubmit={onSubmit}>
      <h2>Nuevo usuario</h2>
      <label>
        Correo
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      <label>
        Contraseña (mínimo 8)
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
      </label>
      <label>
        Rol
        <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
          {(Object.keys(ROLE_LABELS) as Role[]).map((r) => (
            <option key={r} value={r}>
              {ROLE_LABELS[r]}
            </option>
          ))}
        </select>
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={busy}>
        Crear
      </button>
    </form>
  )
}
