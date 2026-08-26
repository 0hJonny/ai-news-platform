import { http } from '@/api/http'
import { useAuthStore } from '@/stores/authStore/authStore'
import { ApiChatsRepository } from './ApiChatsRepository'
import type { IChatsRepository } from './IChatsRepository'

export function createChatsRepository(httpClient = http): IChatsRepository {
  const getToken = () => {
    const authStore = useAuthStore()
    return authStore.token
  }

  return new ApiChatsRepository(httpClient, getToken)
}

export { ApiChatsRepository }
export type { IChatsRepository }
