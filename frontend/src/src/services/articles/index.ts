import { http } from '@/api/http' // Make sure this points to your axios instance
import type { IArticlesRepository } from './IArticlesRepository'
// import { MockArticlesRepository } from './MockArticlesRepository'
import { ApiArticlesRepository } from './ApiArticlesRepository'

export function createArticlesRepository(httpClient = http): IArticlesRepository {
  // Uncomment if you're using mocks for tests or local development
  // const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true'
  // if (useMockData) {
  //   return new MockArticlesRepository()
  // }

  return new ApiArticlesRepository(httpClient)
}

export const articlesRepository = createArticlesRepository()

export { ApiArticlesRepository }
export type { IArticlesRepository }
