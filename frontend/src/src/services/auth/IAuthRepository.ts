import type {
  AuthRequest,
  AuthResult,
  LoginAvailabilityResult,
  ProfileResult,
  UsernameCheckResult,
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
  // The Username Suggestion Engine: like checkLoginAvailability, but a
  // taken handle comes back with a few DB-verified free alternatives in
  // the same round trip. Same debounce/AbortSignal contract.
  checkUsername(query: string, signal?: AbortSignal): Promise<UsernameCheckResult>
}
