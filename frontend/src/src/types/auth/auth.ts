// Matches Go: AuthRequest
export interface AuthRequest {
  email?: string
  password?: string
  name?: string
  login?: string
}

// Matches Go: TokenResponse
export interface TokenResponse {
  token: string
  expires_at: number
}

// Matches Go: UserResponse (GET /auth/user)
export interface UserProfile {
  id: string
  email: string
  name: string
  login: string
  role: string
}

export interface LoginAvailability {
  available: boolean
}

export type LoginAvailabilityResult =
  { success: true; data: LoginAvailability } | { success: false; error: RepositoryError }

// Matches Go: CheckUsernameResponse — the register form's "Username
// Suggestion Engine" endpoint. suggestions is only populated (and only
// meaningful) when available is false.
export interface UsernameCheckResponse {
  available: boolean
  suggestions?: string[]
}

export type UsernameCheckResult =
  { success: true; data: UsernameCheckResponse } | { success: false; error: RepositoryError }

export interface RepositoryError {
  code: string
  message: string
  details?: Record<string, unknown>
}

// A confirmation step the backend can demand mid-flow (email link, SMS/TOTP
// code, etc.) before issuing a real token. No endpoint emits this yet, but
// the repository/store already branch on it so a real step can be wired in
// later without reshaping this contract.
export interface VerificationChallenge {
  method: 'email' | 'sms' | 'totp'
  // Masked destination to show the user, e.g. "j***@example.com"
  target: string
}

export type AuthOutcome =
  | { kind: 'authenticated'; data: TokenResponse }
  | { kind: 'verification_required'; challenge: VerificationChallenge }

export type AuthResult =
  { success: true; data: AuthOutcome } | { success: false; error: RepositoryError }

export type ProfileResult =
  { success: true; data: UserProfile } | { success: false; error: RepositoryError }
