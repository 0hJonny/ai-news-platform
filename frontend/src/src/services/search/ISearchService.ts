import type { Article } from '@/types/article/article'
import type { SearchQuery, SearchFilters, SearchOptions, SearchResult } from '@/types/search/search'

export interface ISearchService {
  /**
   * Search articles
   */
  search(query: SearchQuery, filters: SearchFilters, options?: SearchOptions): Promise<SearchResult>

  /**
   * Get popular tags
   */
  getPopularTags(locale: string): Promise<string[]>

  /**
   * Get similar articles
   */
  getSimilarArticles(articleId: string, locale: string, limit?: number): Promise<Article[]>
}
