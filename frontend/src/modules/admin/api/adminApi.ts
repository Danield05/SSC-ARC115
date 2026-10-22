import { apiFetch, jsonBody } from '../../../shared/api/client'
import type { Role, User } from '../../auth/types'
import type { Device, DeviceCreated, NewDevice, NewUser } from '../types'

export const listDevices = () => apiFetch<Device[]>('/devices')

export const createDevice = (data: NewDevice) =>
  apiFetch<DeviceCreated>('/devices', { method: 'POST', ...jsonBody(data) })

export const updateDevice = (id: string, changes: Partial<Pick<Device, 'name' | 'promoter_email' | 'active'>>) =>
  apiFetch<Device>(`/devices/${encodeURIComponent(id)}`, { method: 'PATCH', ...jsonBody(changes) })

export const rotateKey = (id: string) =>
  apiFetch<{ device_id: string; api_key: string }>(`/devices/${encodeURIComponent(id)}/rotate-key`, {
    method: 'POST',
  })

export const listUsers = () => apiFetch<User[]>('/users')

export const createUser = (data: NewUser) =>
  apiFetch<User>('/users', { method: 'POST', ...jsonBody(data) })

export const updateUser = (email: string, changes: { active?: boolean; role?: Role }) =>
  apiFetch<User>(`/users/${encodeURIComponent(email)}`, { method: 'PATCH', ...jsonBody(changes) })

export const resendInvite = (email: string) =>
  apiFetch<User>(`/users/${encodeURIComponent(email)}/resend-invite`, { method: 'POST' })
