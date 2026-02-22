import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

// Attach JWT token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// Types
export interface Instance {
  id: string
  name: string
  webhook_path: string
  calcom_event_type_id?: number
  calcom_api_key_configured: boolean
  timezone: string
  timezone_offset: string
  business_name: string
  workday_start: string
  workday_end: string
  is_active: boolean
  created_at: string
  updated_at: string
  // Per-instance SMTP
  smtp_host?: string
  smtp_port?: number
  smtp_user?: string
  smtp_from_email?: string
  smtp_configured: boolean
}

export interface GlobalSettings {
  llm_provider: string
  llm_base_url: string
  llm_api_key_set: boolean
  llm_model: string
  updated_at: string
  provider_keys_set: Record<string, boolean>
  smtp_host?: string
  smtp_port?: number
  smtp_user?: string
  smtp_from_email?: string
  smtp_configured: boolean
}

export interface GuestRecord {
  id: number
  instance_id: string
  name?: string
  email: string
  pin_code: string
  booking_time?: string
  status: string
  meeting_title?: string
  calendar_event_id?: string
  created_at: string
  updated_at: string
}

export interface Session {
  session_id: string
  updated_at: string
  message_count: number
}
