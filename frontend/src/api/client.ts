import axios, { type InternalAxiosRequestConfig } from 'axios'
import { ref } from 'vue'
import authClient from './authClient'
import type { TokenResponse } from '@/types'

/**
 * Shared reactive access token.
 *
 * Defined here (not in the auth store) so the axios interceptor can read and
 * write it without importing useAuthStore — which would create a circular
 * dependency (client → store → api/index → client).
 *
 * The auth store imports this ref directly and treats it as its own state.
 */
export const accessToken = ref<string | null>(null)

const apiClient = axios.create({
  baseURL: (import.meta.env.VITE_API_URL as string | undefined) ?? '/api',
  timeout: 60000,
  withCredentials: true, // sends the HttpOnly refresh-token cookie automatically
})

// ── Refresh queue ─────────────────────────────────────────────────────────────
// Prevents duplicate /auth/refresh calls when multiple requests 401 at the same time.
let isRefreshing = false
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

function processQueue(error: unknown, token: string | null): void {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token!)
  })
  failedQueue = []
}

// ── Request: attach in-memory access token ────────────────────────────────────
apiClient.interceptors.request.use((config) => {
  if (accessToken.value) {
    config.headers.Authorization = `Bearer ${accessToken.value}`
  }
  return config
})

// ── Response: silently refresh on 401, then retry original request ────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    const is401 = error.response?.status === 401
    // Never retry auth endpoints to prevent infinite loops
    const isAuthEndpoint = (original.url ?? '').includes('/auth/')

    if (is401 && !original._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        // Park this request until the in-flight refresh completes
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          original.headers.Authorization = `Bearer ${token}`
          return apiClient(original)
        })
      }

      original._retry = true
      isRefreshing = true

      try {
        const { data } = await authClient.post<TokenResponse>('/auth/refresh')
        accessToken.value = data.access_token
        processQueue(null, data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(original)
      } catch (refreshError) {
        processQueue(refreshError, null)
        accessToken.value = null
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default apiClient
