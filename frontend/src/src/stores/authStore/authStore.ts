import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createAuthRepository } from '@/services/auth'
import type { AuthRequest } from '@/types/auth/auth'

export const useAuthStore = defineStore('auth', () => {
  const repo = createAuthRepository()

  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<undefined | null>(null)

  const errorCode = ref<string | null>(null)
  const errorDetails = ref<Record<string, unknown> | null>(null)
  const isLoading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  const _clearErrors = () => {
    errorCode.value = null
    errorDetails.value = null
  }

  const _handleSuccess = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
    // For future use: await getUserProfile()
    return true
  }

  const _handleError = (error: { code: string; details?: Record<string, unknown> }) => {
    errorCode.value = error.code
    errorDetails.value = error.details || null
    return false
  }

  const login = async (credentials: AuthRequest) => {
    isLoading.value = true
    _clearErrors()

    const result = await repo.login(credentials)
    isLoading.value = false

    if (result.success) {
      return _handleSuccess(result.data.token)
    }
    return _handleError(result.error)
  }

  const register = async (credentials: AuthRequest) => {
    isLoading.value = true
    _clearErrors()

    const result = await repo.register(credentials)
    isLoading.value = false

    if (result.success) {
      return _handleSuccess(result.data.token)
    }
    return _handleError(result.error)
  }

  const anonymousLogin = async () => {
    isLoading.value = true
    _clearErrors()

    const result = await repo.anonymousLogin()
    isLoading.value = false

    if (result.success) {
      return _handleSuccess(result.data.token)
    }
    return _handleError(result.error)
  }

  const logout = () => {
    // If the backend gets a /logout endpoint, add it to the repository
    // repo.logout().catch(() => {})
    $reset()
  }

  const $reset = () => {
    token.value = null
    user.value = null
    _clearErrors()
    isLoading.value = false
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    errorCode,
    errorDetails,
    isLoading,
    isAuthenticated,
    register,
    login,
    anonymousLogin,
    logout,
    $reset,
  }
})
