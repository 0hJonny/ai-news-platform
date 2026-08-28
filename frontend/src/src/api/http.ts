import axios from 'axios'
import { useAuthStore } from '@/stores/authStore/authStore'
import { API_BASE_URL, ENDPOINTS } from './endpoints'

export const http = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// Requests where a 401 means "bad credentials", not "your session expired" —
// the session-expired modal must not fire while someone is just logging in.
const PUBLIC_AUTH_ENDPOINTS: string[] = [ENDPOINTS.LOGIN, ENDPOINTS.REGISTER, ENDPOINTS.ANONIMOUS]

http.interceptors.response.use(
  (r) => r,
  (err) => {
    console.error('Axios error:', {
      message: err.message,
      code: err.code,
      url: err.config?.url,
    })

    const url: string = err.config?.url || ''
    const isPublicAuthCall = PUBLIC_AUTH_ENDPOINTS.some((endpoint) => url.includes(endpoint))
    const status: number | undefined = err.response?.status
    const backendErrorCode: string | undefined = err.response?.data?.error?.code

    // Only react to the exact (status, code) pairs the backend uses for a
    // token that was actually sent and rejected. A 401 without TOKEN_EXPIRED
    // (e.g. TOKEN_MISSING, or a guest endpoint that just requires auth) must
    // not be treated as "your session expired" — that's a different, expected
    // case and popping the modal for it is a false positive.
    if (!isPublicAuthCall) {
      if (status === 403 && backendErrorCode === 'TOKEN_INVALID') {
        // Token was never legitimately issued (hand-edited, bad signature).
        useAuthStore().notifyInvalidSession()
      } else if (status === 401 && backendErrorCode === 'TOKEN_EXPIRED') {
        useAuthStore().notifySessionExpired()
      }
    }

    return Promise.reject(err)
  },
)

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})
