import { apiFetch, jsonBody } from '../../../shared/api/client'
import type { LoginResponse, User } from '../types'

export const login = (email: string, password: string) =>
  apiFetch<LoginResponse>('/auth/login', { method: 'POST', ...jsonBody({ email, password }) })

export const fetchMe = () => apiFetch<User>('/auth/me')
