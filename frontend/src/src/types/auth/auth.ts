// Matches Go: AuthRequest
export interface AuthRequest {
  email?: string
  password?: string
}

// Matches Go: TokenResponse
export interface TokenResponse {
  token: string
  expires_at: number
}

export interface RepositoryError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export type AuthResult =
  | { success: true; data: TokenResponse }
  | { success: false; error: RepositoryError }
