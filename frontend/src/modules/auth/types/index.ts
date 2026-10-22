export type Role = 'admin' | 'promoter' | 'viewer'

export interface User {
  email: string
  name: string
  role: Role
  active: boolean
  created_at: string
  /** Verdadero mientras la persona use una contraseña provisional. */
  must_change_password: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Administrador',
  promoter: 'Promotor',
  viewer: 'Evaluador (solo lectura)',
}

export const ROLE_OPTIONS = (Object.keys(ROLE_LABELS) as Role[]).map((value) => ({
  value,
  label: ROLE_LABELS[value],
}))
