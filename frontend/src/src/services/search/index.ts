import { http } from '@/api/http' // Make sure this points to your axios client
import type { AxiosInstance } from 'axios'
import type { ISearchService } from './ISearchService'
import { MockSearchService } from './MockSearchService'
import { ApiSearchService } from './ApiSearchService'

/**
 * Data source type
 */
type SearchServiceType = 'mock' | 'api'

/**
 * Configuration:
 * First check the search-specific flag.
 * If it's not set, fall back to the app-wide mock flag.
 */
const SERVICE_TYPE: SearchServiceType =
  (import.meta.env.VITE_SEARCH_SERVICE as SearchServiceType) ||
  (import.meta.env.VITE_USE_MOCK_DATA === 'true' ? 'mock' : 'api')

/**
 * Factory for creating the search service (Singleton)
 */
class SearchServiceFactory {
  private static instance: ISearchService | null = null

  /**
   * Get the service instance.
   * Accepts an httpClient to allow injection in tests.
   */
  static getInstance(httpClient: AxiosInstance = http): ISearchService {
    if (!this.instance) {
      switch (SERVICE_TYPE) {
        case 'api':
          // Pass the configured axios instance to the real service
          this.instance = new ApiSearchService(httpClient)
          console.info('🔌 Using API Search Service')
          break
        case 'mock':
        default:
          this.instance = new MockSearchService()
          console.info('🎭 Using Mock Search Service')
          break
      }
    }
    return this.instance
  }

  /**
   * For tests - allows explicitly setting a mocked service
   */
  static setInstance(service: ISearchService): void {
    this.instance = service
  }

  /**
   * Reset the instance (to clean up state between tests)
   */
  static reset(): void {
    this.instance = null
  }
}

// Export the ready-made instance to be used in searchStore
export const searchService = SearchServiceFactory.getInstance()

export { SearchServiceFactory, ApiSearchService, MockSearchService }
export type { ISearchService }
