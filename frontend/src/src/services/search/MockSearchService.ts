import type { ISearchService } from './ISearchService'
import type { Article } from '@/types/article/article'
import type { SearchQuery, SearchFilters, SearchOptions, SearchResult } from '@/types/search/search'
import { mockArticles } from '@/stores/article/mock/articles'

export class MockSearchService implements ISearchService {
  /**
   * Delay to simulate an API request
   */
  private async delay(ms: number = 300): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, ms))
  }

  /**
   * Search articles
   */
  async search(
    query: SearchQuery,
    filters: SearchFilters,
    options: SearchOptions = {},
  ): Promise<SearchResult> {
    await this.delay()

    let results = mockArticles.filter((article) => article.languageCode === filters.locale)

    // Filter by category
    if (filters.category) {
      results = results.filter((article) => article.category === filters.category)
    }

    // Search by text
    if (query.text.trim()) {
      const searchText = query.text.toLowerCase()
      results = results.filter(
        (article) =>
          article.title.toLowerCase().includes(searchText) ||
          article.content.toLowerCase().includes(searchText) ||
          article.category.toLowerCase().includes(searchText),
      )
    }

    // Filter by tags (all tags must match)
    if (query.tags.length > 0) {
      results = results.filter((article) =>
        query.tags.every((searchTag) =>
          article.tags.some((articleTag) =>
            articleTag.toLowerCase().includes(searchTag.toLowerCase().replace('#', '')),
          ),
        ),
      )
    }

    const total = results.length

    // Apply pagination if parameters are provided
    if (options.page && options.limit) {
      const start = (options.page - 1) * options.limit
      const end = start + options.limit
      results = results.slice(start, end)
    }

    return {
      articles: results,
      total,
    }
  }

  /**
   * Get popular tags
   */
  async getPopularTags(locale: string): Promise<string[]> {
    await this.delay(200)

    const articles = mockArticles.filter((article) => article.languageCode === locale)

    // Count tag frequency
    const tagCount = new Map<string, number>()

    articles.forEach((article) => {
      article.tags.forEach((tag) => {
        const count = tagCount.get(tag) || 0
        tagCount.set(tag, count + 1)
      })
    })

    // Sort by popularity and return top 10
    return Array.from(tagCount.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([tag]) => tag)
  }

  /**
   * Get similar articles
   */
  async getSimilarArticles(
    articleId: string,
    locale: string,
    limit: number = 5,
  ): Promise<Article[]> {
    await this.delay(200)

    const article = mockArticles.find((a) => a.id === articleId)
    if (!article) return []

    // Look for articles with similar tags
    const similar = mockArticles
      .filter(
        (a) =>
          a.id !== articleId &&
          a.languageCode === locale &&
          a.tags.some((tag) => article.tags.includes(tag)),
      )
      .slice(0, limit)

    return similar
  }
}
