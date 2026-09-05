import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createAuthRepository } from '@/services/auth'
import type {
  AuthOutcome,
  AuthRequest,
  UserProfile,
  VerificationChallenge,
} from '@/types/auth/auth'

// What login()/register() resolve to once the server responds successfully:
// either a real session, or a mid-flow confirmation step (see
// VerificationChallenge). `false` (returned by the callers below on error)
// stays separate so callers can `if (result)` without a type guard.
export type AuthFlowStatus = 'authenticated' | 'verification_required'

export const useAuthStore = defineStore('auth', () => {
  const repo = createAuthRepository()

  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserProfile | null>(null)

  // Whether the current/last identity was a guest (anonymous login) rather
  // than a real registered account. Unlike token, this survives
  // notifySessionExpired/notifyInvalidSession on purpose — those clear the
  // token but the modals still need to know whether to offer "log back in"
  // (real account) or just mint a fresh guest session (was already a guest).
  const isGuest = ref<boolean>(localStorage.getItem('isGuest') !== 'false')

  // Set when login/register comes back asking for an extra confirmation
  // step instead of a token. Nothing produces this today (see AuthOutcome),
  // so it's always null in practice — it's here so a verification screen has
  // somewhere to read the challenge from once the backend supports one.
  const pendingVerification = ref<VerificationChallenge | null>(null)

  const errorCode = ref<string | null>(null)
  const errorDetails = ref<Record<string, unknown> | null>(null)
  const isLoading = ref(false)

  // Recoverable: token expired normally. Modal offers login/register/guest.
  const sessionExpired = ref(false)
  // Fatal: token was never legitimately issued (bad signature, hand-edited,
  // etc). Modal offers re-login for a real account, or starting over as a
  // guest if the session was already anonymous (see isGuest).
  const invalidSession = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  const clearErrors = () => {
    errorCode.value = null
    errorDetails.value = null
  }

  const _handleSuccess = (newToken: string, guest: boolean) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
    isGuest.value = guest
    localStorage.setItem('isGuest', String(guest))
    // A fresh, legitimate token means whatever put us into either of the
    // "no longer trust the old token" states has been resolved.
    sessionExpired.value = false
    invalidSession.value = false
    return true
  }

  const _handleError = (error: { code: string; details?: Record<string, unknown> }) => {
    errorCode.value = error.code
    errorDetails.value = error.details || null
    return false
  }

  // Shared by login/register/anonymousLogin: applies whichever branch of
  // AuthOutcome the server returned.
  const _applyOutcome = (outcome: AuthOutcome, guest: boolean): AuthFlowStatus => {
    if (outcome.kind === 'verification_required') {
      pendingVerification.value = outcome.challenge
      return 'verification_required'
    }
    pendingVerification.value = null
    _handleSuccess(outcome.data.token, guest)
    return 'authenticated'
  }

  const login = async (credentials: AuthRequest) => {
    isLoading.value = true
    clearErrors()

    const result = await repo.login(credentials)
    isLoading.value = false

    if (result.success) {
      return _applyOutcome(result.data, false)
    }
    return _handleError(result.error)
  }

  const register = async (credentials: AuthRequest) => {
    isLoading.value = true
    clearErrors()

    const result = await repo.register(credentials)
    isLoading.value = false

    if (result.success) {
      return _applyOutcome(result.data, false)
    }
    return _handleError(result.error)
  }

  // Not gated by isLoading/errorCode on purpose — this is a debounced,
  // read-only lookup the register form fires on every settled keystroke of
  // the login field, and it shouldn't disable the submit button or clobber
  // an unrelated error already on screen. Param named loginValue, not
  // login, so it doesn't shadow the login() action above.
  const checkLoginAvailability = (loginValue: string, signal?: AbortSignal) => {
    return repo.checkLoginAvailability(loginValue, signal)
  }

  // Same shape as checkLoginAvailability above, but backs the Username
  // Suggestion Engine: a taken handle comes back with DB-verified
  // alternatives in the same round trip.
  const checkUsername = (query: string, signal?: AbortSignal) => {
    return repo.checkUsername(query, signal)
  }

  const anonymousLogin = async () => {
    isLoading.value = true
    clearErrors()

    const result = await repo.anonymousLogin()
    isLoading.value = false

    if (result.success) {
      return _applyOutcome(result.data, true) === 'authenticated'
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
    isGuest.value = true
    localStorage.removeItem('isGuest')
    pendingVerification.value = null
    clearErrors()
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

  // Loads the current user's profile (email/name/role). Safe to call
  // whenever a token exists; failures are logged but don't affect auth
  // state itself — the sidebar just keeps showing its fallback nickname.
  const fetchProfile = async () => {
    if (!token.value) return
    const result = await repo.getProfile()
    if (result.success) {
      user.value = result.data
    } else {
      console.error('[AuthStore] Failed to load profile:', result.error.message)
    }
  }

  return {
    token,
    user,
    isGuest,
    pendingVerification,
    errorCode,
    errorDetails,
    isLoading,
    sessionExpired,
    invalidSession,
    isAuthenticated,
    register,
    login,
    checkLoginAvailability,
    checkUsername,
    anonymousLogin,
    logout,
    notifySessionExpired,
    notifyInvalidSession,
    dismissSessionExpired,
    clearErrors,
    fetchProfile,
    $reset,
  }
})
