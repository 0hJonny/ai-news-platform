import type { AuthRequest, AuthResult } from '@/types/auth/auth'

export interface IAuthRepository {
  login(credentials: AuthRequest): Promise<AuthResult>
  register(credentials: AuthRequest): Promise<AuthResult>
  anonymousLogin(): Promise<AuthResult>
}
