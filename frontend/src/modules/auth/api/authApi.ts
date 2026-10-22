import { apiFetch, jsonBody } from '../../../shared/api/client'
import type { LoginResponse, User } from '../types'

export const login = (email: string, password: string) =>
  apiFetch<LoginResponse>('/auth/login', { method: 'POST', ...jsonBody({ email, password }) })

export const fetchMe = () => apiFetch<User>('/auth/me')

export const forgotPassword = (email: string) =>
  apiFetch<{ message: string }>('/auth/forgot-password', { method: 'POST', ...jsonBody({ email }) })

export const changePassword = (current_password: string, new_password: string) =>
  apiFetch<User>('/auth/change-password', {
    method: 'POST',
    ...jsonBody({ current_password, new_password }),
  })
