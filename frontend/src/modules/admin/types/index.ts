import type { Role } from '../../auth/types'

export interface Device {
  device_id: string
  name: string
  promoter_email: string
  active: boolean
  created_at: string
}

export interface DeviceCreated extends Device {
  api_key: string
}

export interface NewDevice {
  device_id: string
  name: string
  promoter_email: string
}

export interface NewUser {
  email: string
  password: string
  role: Role
}
