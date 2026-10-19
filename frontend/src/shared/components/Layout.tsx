import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../modules/auth/hooks/useAuth'
import { ROLE_LABELS } from '../../modules/auth/types'

export default function Layout() {
  const { user, logout } = useAuth()
  if (!user) return null

  return (
    <>
      <header className="topbar">
        <strong>SSC-ARC115</strong>
        <nav>
          <NavLink to="/" end>
            Pacientes
          </NavLink>
          {(user.role === 'admin' || user.role === 'viewer') && (
            <NavLink to="/admin/devices">Dispositivos</NavLink>
          )}
          {user.role === 'admin' && <NavLink to="/admin/users">Usuarios</NavLink>}
        </nav>
        <span className="topbar-user">
          {user.email} · {ROLE_LABELS[user.role]}
          <button type="button" onClick={logout}>
            Salir
          </button>
        </span>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  )
}
