import type { AxiosInstance } from 'axios'
import type { IAuthRepository } from './IAuthRepository'
import type {
  AuthOutcome,
  AuthRequest,
  AuthResult,
  LoginAvailability,
  LoginAvailabilityResult,
  ProfileResult,
  TokenResponse,
  UserProfile,
  VerificationChallenge,
} from '@/types/auth/auth'
import { getErrorCode } from '@/utils/errorMapper'
import { ENDPOINTS } from '@/api/endpoints'

function hasStringError(obj: unknown): obj is { error: string } {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'error' in obj &&
    typeof (obj as Record<string, unknown>).error === 'string'
  )
}

interface VerificationRequiredResponse {
  requires_verification: VerificationChallenge
}

function isVerificationRequiredResponse(data: unknown): data is VerificationRequiredResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    'requires_verification' in data &&
    typeof (data as Record<string, unknown>).requires_verification === 'object'
  )
}

// Named once instead of inlined per catch block below, so "we couldn't even
// parse the server's error" always carries the same code/text rather than
// each method quietly drifting from the others.
const FALLBACK_ERROR_CODE = 'AUTH_HTTP_ERROR'
const FALLBACK_ERROR_MESSAGES = {
  auth: 'Ошибка аутентификации',
  profile: 'Ошибка получения профиля',
  loginAvailability: 'Не удалось проверить доступность логина',
} as const

export class ApiAuthRepository implements IAuthRepository {
  constructor(private readonly http: AxiosInstance) {}

  async login(credentials: AuthRequest): Promise<AuthResult> {
    return this._execute(ENDPOINTS.LOGIN, credentials)
  }

  async register(credentials: AuthRequest): Promise<AuthResult> {
    return this._execute(ENDPOINTS.REGISTER, credentials)
  }

  async anonymousLogin(): Promise<AuthResult> {
    return this._execute(ENDPOINTS.ANONIMOUS)
  }

  async checkLoginAvailability(
    login: string,
    signal?: AbortSignal,
  ): Promise<LoginAvailabilityResult> {
    try {
      const { data } = await this.http.get<LoginAvailability>(ENDPOINTS.LOGIN_AVAILABLE, {
        params: { login },
        signal,
      })
      return { success: true, data }
    } catch (e: unknown) {
      const { code, details } = getErrorCode(e)
      return {
        success: false,
        error: {
          code: code || FALLBACK_ERROR_CODE,
          message: FALLBACK_ERROR_MESSAGES.loginAvailability,
          details: details || undefined,
        },
      }
    }
  }

  async getProfile(): Promise<ProfileResult> {
    try {
      const { data } = await this.http.get<UserProfile>(ENDPOINTS.USERDATA)
      return { success: true, data }
    } catch (e: unknown) {
      const { code, details } = getErrorCode(e)
      return {
        success: false,
        error: {
          code: code || FALLBACK_ERROR_CODE,
          message: FALLBACK_ERROR_MESSAGES.profile,
          details: details || undefined,
        },
      }
    }
  }

  private async _execute(endpoint: string, payload?: unknown): Promise<AuthResult> {
    try {
      const { data } = await this.http.post<TokenResponse | VerificationRequiredResponse>(
        endpoint,
        payload,
      )
      const outcome: AuthOutcome = isVerificationRequiredResponse(data)
        ? { kind: 'verification_required', challenge: data.requires_verification }
        : { kind: 'authenticated', data: data as TokenResponse }
      return { success: true, data: outcome }
    } catch (e: unknown) {
      const { code, details } = getErrorCode(e)

      const errorMessage = hasStringError(details) ? details.error : FALLBACK_ERROR_MESSAGES.auth

      const safeDetails =
        typeof details === 'object' && details !== null
          ? (details as Record<string, unknown>)
          : undefined

      return {
        success: false,
        error: {
          code: code || FALLBACK_ERROR_CODE,
          message: errorMessage,
          details: safeDetails,
        },
      }
    }
  }
}
