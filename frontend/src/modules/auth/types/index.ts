export type Role = 'admin' | 'promoter' | 'viewer'

export interface User {
  email: string
  role: Role
  active: boolean
  created_at: string
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
