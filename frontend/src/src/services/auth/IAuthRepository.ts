import type {
  AuthRequest,
  AuthResult,
  LoginAvailabilityResult,
  ProfileResult,
} from '@/types/auth/auth'

export interface IAuthRepository {
  login(credentials: AuthRequest): Promise<AuthResult>
  register(credentials: AuthRequest): Promise<AuthResult>
  anonymousLogin(): Promise<AuthResult>
  getProfile(): Promise<ProfileResult>
  // Read-only availability check for the register form's login field. Takes
  // an AbortSignal because it's called on a debounce as the user types —
  // every new keystroke should cancel whatever check is still in flight
  // rather than let stale responses race with the latest one.
  checkLoginAvailability(login: string, signal?: AbortSignal): Promise<LoginAvailabilityResult>
}
