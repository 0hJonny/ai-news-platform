import { http } from '@/api/http'
import { ApiAuthRepository } from './ApiAuthRepository'
import type { IAuthRepository } from './IAuthRepository'

export function createAuthRepository(httpClient = http): IAuthRepository {
  return new ApiAuthRepository(httpClient)
}

export { ApiAuthRepository }
export type { IAuthRepository }
