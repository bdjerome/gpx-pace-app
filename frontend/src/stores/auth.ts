import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import type { UserProfile, LoginRequest, RegisterRequest } from '@/types'

function isTokenExpired(token: string): boolean {
  try {
    const segment = token.split('.')[1]
    if (!segment) return true
    // JWT uses base64url — normalize to standard base64 before decoding
    const base64 = segment.replace(/-/g, '+').replace(/_/g, '/').padEnd(
      segment.length + ((4 - (segment.length % 4)) % 4),
      '=',
    )
    const payload = JSON.parse(atob(base64))
    console.log('Token payload:', payload)
    return typeof payload.exp === 'number' && payload.exp * 1000 < Date.now()
  } catch (error) {
    console.error('Error decoding token:', error)
    return true // malformed token — treat as expired
  }
}

function loadToken(key: string): string | null {
  const token = localStorage.getItem(key)
  if (!token || isTokenExpired(token)) {
    localStorage.removeItem(key)
    return null
  }
  return token
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(loadToken('access_token'))
  const refreshToken = ref<string | null>(loadToken('refresh_token'))
  const user = ref<UserProfile | null>(null)

  // Computed property to check if user is authenticated based on presence and validity of access token
  const isAuthenticated = computed(
    () => !!accessToken.value && !isTokenExpired(accessToken.value),
  )

  // Persist tokens to localStorage and update reactive state
  function _persist(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  async function login(credentials: LoginRequest) {
    const { data } = await authApi.login(credentials)
    _persist(data.access_token, data.refresh_token)
  }

  async function register(payload: RegisterRequest) {
    const { data } = await authApi.register(payload)
    user.value = data
    // Registration does not return a token — caller redirects to login
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { accessToken, refreshToken, user, isAuthenticated, login, register, logout }
})
