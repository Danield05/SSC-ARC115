import { useState } from 'react'
import { useAuth } from '../../auth/hooks/useAuth'
import { ROLE_LABELS } from '../../auth/types'
import UserForm from '../components/UserForm'
import { useUsers } from '../hooks/useUsers'

export default function UsersPage() {
  const { user: me } = useAuth()
  const { users, loading, error, create, setActive } = useUsers()
  const [actionError, setActionError] = useState('')

  async function toggle(email: string, active: boolean) {
    setActionError('')
    try {
      await setActive(email, active)
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'La acción falló.')
    }
  }

  return (
    <>
      <h1>Usuarios</h1>
      <UserForm onCreate={create} />
      {error && <p className="error">{error}</p>}
      {actionError && <p className="error">{actionError}</p>}
      {loading ? (
        <p>Cargando…</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Correo</th>
              <th>Rol</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.email}>
                <td>{u.email}</td>
                <td>{ROLE_LABELS[u.role]}</td>
                <td>{u.active ? 'Activo' : 'Desactivado'}</td>
                <td>
                  {u.email !== me?.email && (
                    <button type="button" className="secondary" onClick={() => toggle(u.email, !u.active)}>
                      {u.active ? 'Desactivar' : 'Activar'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}
