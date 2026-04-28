import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { accessToken } from '@/api/client'
import { authApi } from '@/api'
import type { UserProfile, LoginRequest, RegisterRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // accessToken is the shared Vue ref from api/client — written here and read
  // by the axios interceptor without needing to import useAuthStore.
  // It lives in memory only; it is never written to localStorage.
  const user = ref<UserProfile | null>(null)
  const isAuthenticated = computed(() => !!accessToken.value)

  /**
   * Called on app startup. Uses the HttpOnly refresh-token cookie (sent
   * automatically by the browser) to obtain a fresh access token.
   * Throws if no valid cookie exists — caller should swallow the error.
   */
  async function silentRefresh(): Promise<void> {
    const { data } = await authApi.refresh()
    accessToken.value = data.access_token
  }

  async function login(credentials: LoginRequest): Promise<void> {
    const { data } = await authApi.login(credentials)
    accessToken.value = data.access_token
  }

  async function register(payload: RegisterRequest): Promise<void> {
    const { data } = await authApi.register(payload)
    user.value = data
  }

  async function logout(): Promise<void> {
    accessToken.value = null
    user.value = null
    try {
      await authApi.logout()
    } catch {
      // Cookie may already be expired — clearing the in-memory token is enough.
    }
  }

  return { accessToken, user, isAuthenticated, silentRefresh, login, register, logout }
})
