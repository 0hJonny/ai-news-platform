// src/services/search/ApiSearchService.ts
import type { AxiosInstance } from 'axios'
import type { Article, ArticleDTO, ApiResponse } from '@/types/article/article'
import type { ISearchService } from './ISearchService'
import type { SearchQuery, SearchFilters, SearchOptions, SearchResult } from '@/types/search/search'

export class ApiSearchService implements ISearchService {
  constructor(private readonly httpClient: AxiosInstance) {}

  /**
   * Mapper DTO -> Article (reusing the logic)
   */
  private mapToArticle(dto: ArticleDTO): Article {
    let parsedTags: string[] = []
    try {
      if (dto.tags) parsedTags = JSON.parse(dto.tags)
    } catch {
      parsedTags = []
    }

    const imageBaseUrl = import.meta.env.VITE_IMAGE_BASE_URL || 'http://localhost:9000'
    return {
      id: dto.id,
      title: dto.title,
      publishedDate: dto.publishedDate,
      category: dto.category,
      tags: parsedTags,
      content: dto.content,
      languageCode: dto.language_code,
      imageSource: `${imageBaseUrl}/images/${dto.id}.png`,
      sourceLink: dto.source_link,
      neuralNetworks: dto.neural_networks,
    }
  }

  /**
   * Builds the backend-specific query string for the Go backend (\text\+!!tag!!)
   */
  private buildQueryString(query: SearchQuery): string {
    let q = ''

    if (query.text.trim()) {
      q += `\\${query.text.trim()}\\`
    }

    if (query.tags.length > 0) {
      query.tags.forEach((tag, index) => {
        if (q !== '' || index > 0) q += '+'
        q += `!!${tag.replace('#', '')}!!`
      })
    }

    return q
  }

  async search(
    query: SearchQuery,
    filters: SearchFilters,
    options: SearchOptions = {},
  ): Promise<SearchResult> {
    const params = {
      language_code: filters.locale,
      category: filters.category,
      page: options.page,
      limit: options.limit,
      query: this.buildQueryString(query),
    }

    const response = await this.httpClient.get<ApiResponse<ArticleDTO[]>>('/g/article/search', {
      params,
    })

    let articles = (response.data.data ?? []).map((dto) => this.mapToArticle(dto))

    // 🛠 FRONTEND FILTER: Force AND logic for tags.
    // If the backend returned articles using OR logic (at least 1 matching tag), trim the extras.
    if (query.tags.length > 1) {
      articles = articles.filter((article) =>
        query.tags.every((searchTag) => {
          const cleanSearchTag = searchTag.replace('#', '').toLowerCase()
          return article.tags.some((articleTag) => articleTag.toLowerCase() === cleanSearchTag)
        }),
      )
    }

    const total =
      articles.length === options.limit ? (options.page || 1) * options.limit + 1 : articles.length

    return {
      articles,
      total,
    }
  }

  async getPopularTags(): Promise<string[]> {
    return [] // TODO: Implement backend endpoint
  }

  async getSimilarArticles(): Promise<Article[]> {
    return [] // TODO: Implement backend endpoint
  }
}
