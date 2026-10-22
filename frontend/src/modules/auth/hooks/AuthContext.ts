import { createContext } from 'react'
import type { User } from '../types'

export interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<User>
  /** Actualiza el usuario de la sesión (por ejemplo, tras cambiar la contraseña). */
  updateUser: (user: User) => void
  logout: () => void
}

export const AuthContext = createContext<AuthState | null>(null)
