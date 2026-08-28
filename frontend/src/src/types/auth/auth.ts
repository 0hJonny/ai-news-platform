// Matches Go: AuthRequest
export interface AuthRequest {
  email?: string
  password?: string
  name?: string
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
  role: string
}

export interface RepositoryError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export type AuthResult =
  | { success: true; data: TokenResponse }
  | { success: false; error: RepositoryError }

export type ProfileResult =
  | { success: true; data: UserProfile }
  | { success: false; error: RepositoryError }
