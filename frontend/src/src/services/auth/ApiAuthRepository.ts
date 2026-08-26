import type { AxiosInstance } from 'axios'
import type { IAuthRepository } from './IAuthRepository'
import type { AuthRequest, AuthResult, TokenResponse } from '@/types/auth/auth'
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

  private async _execute(endpoint: string, payload?: unknown): Promise<AuthResult> {
    try {
      const { data } = await this.http.post<TokenResponse>(endpoint, payload)
      return { success: true, data }
    } catch (e: unknown) {
      const { code, details } = getErrorCode(e)

      let errorMessage = 'Ошибка аутентификации'

      if (hasStringError(details)) {
        errorMessage = details.error
      }

      const safeDetails =
        typeof details === 'object' && details !== null
          ? (details as Record<string, unknown>)
          : undefined

      return {
        success: false,
        error: {
          code: code || 'AUTH_HTTP_ERROR',
          message: errorMessage,
          details: safeDetails,
        },
      }
    }
  }
}
