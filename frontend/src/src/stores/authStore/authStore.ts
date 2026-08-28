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

  // Recoverable: token expired normally. Modal offers login/register/guest.
  const sessionExpired = ref(false)
  // Fatal: token was never legitimately issued (bad signature, hand-edited,
  // etc). Modal blocks the UI with a single "start over" action.
  const invalidSession = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  const _clearErrors = () => {
    errorCode.value = null
    errorDetails.value = null
  }

  const _handleSuccess = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
    // A fresh, legitimate token means whatever put us into either of the
    // "no longer trust the old token" states has been resolved.
    sessionExpired.value = false
    invalidSession.value = false
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
    sessionExpired.value = false
    invalidSession.value = false
    localStorage.removeItem('token')
  }

  // Called by the http interceptor whenever a request comes back with the
  // ordinary "token expired" signal (401 / TOKEN_EXPIRED). Clears the stale
  // token so isAuthenticated flips false, and raises the flag the
  // session-expired modal is bound to. sessionExpired is intentionally left
  // set even after the user navigates to /login or /register from the modal —
  // it's only cleared by a real re-auth (_handleSuccess) or by explicitly
  // continuing as a guest. That's what stops SidebarChat's guarded
  // auto-anonymous-login from silently minting a brand new guest session
  // (and orphaning the current chat history) if the user hits "back" mid-flow.
  const notifySessionExpired = () => {
    token.value = null
    localStorage.removeItem('token')
    sessionExpired.value = true
  }

  // Called whenever the backend rejects the token as never having been
  // legitimately issued (403 / TOKEN_INVALID) — e.g. a hand-edited JWT.
  // This is a harder failure than a normal expiry, so it takes priority
  // over the recoverable session-expired modal.
  const notifyInvalidSession = () => {
    token.value = null
    localStorage.removeItem('token')
    sessionExpired.value = false
    invalidSession.value = true
  }

  const dismissSessionExpired = () => {
    sessionExpired.value = false
  }

  return {
    token,
    user,
    errorCode,
    errorDetails,
    isLoading,
    sessionExpired,
    invalidSession,
    isAuthenticated,
    register,
    login,
    anonymousLogin,
    logout,
    notifySessionExpired,
    notifyInvalidSession,
    dismissSessionExpired,
    $reset,
  }
})
