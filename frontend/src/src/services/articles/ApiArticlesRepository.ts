import type { AxiosInstance } from 'axios'
import type {
  Article,
  ArticleDTO,
  ArticlesFilters,
  ApiResponse,
  CountResponse,
  ArticleQueryParams,
} from '@/types/article/article'
import type { IArticlesRepository } from './IArticlesRepository'

export class ApiArticlesRepository implements IArticlesRepository {
  constructor(private readonly httpClient: AxiosInstance) {}

  /**
   * Mapper: turns a DTO (snake_case, stringified JSON) into a clean Article model
   */
  /**
   * Mapper: turns a DTO into a clean Article model
   */
  private mapToArticle(dto: ArticleDTO): Article {
    let parsedTags: string[] = []

    try {
      if (dto.tags) {
        parsedTags = JSON.parse(dto.tags)
      }
    } catch (e) {
      console.error(`[ApiArticlesRepository] Failed to parse tags for article ${dto.id}:`, e)
      parsedTags = []
    }

    // Build the image URL based on the article ID.
    // If VITE_IMAGE_BASE_URL is not set in .env, default to localhost:9000
    const imageBaseUrl = import.meta.env.VITE_IMAGE_BASE_URL || 'http://localhost:9000'
    const imageUrl = `${imageBaseUrl}/images/${dto.id}.png`

    return {
      id: dto.id,
      title: dto.title,
      publishedDate: dto.publishedDate,
      category: dto.category,
      tags: parsedTags,
      content: dto.content,
      languageCode: dto.language_code,

      // Ignore dto.image_source and use our own constructed URL instead
      imageSource: imageUrl,

      sourceLink: dto.source_link,
      neuralNetworks: dto.neural_networks,
    }
  }

  /**
   * Helper that builds the search query string in the backend's expected format
   */
  private buildSearchQuery(search?: string, tags?: string | string[]): string {
    let query = ''
    if (search) query += `\\${search}\\`

    if (tags) {
      const tagsArray = Array.isArray(tags) ? tags : [tags]
      if (tagsArray.length > 0) {
        if (query !== '') query += '+'
        query += tagsArray.map((tag) => `!!${tag.replace('#', '')}!!`).join('+')
      }
    }
    return query
  }

  async getArticles(locale: string, filters?: ArticlesFilters): Promise<Article[]> {
    const isSearch = Boolean(filters?.search || filters?.tag)
    const endpoint = isSearch ? '/g/article/search' : '/g/articles'

    const params: ArticleQueryParams = {
      language_code: locale,
      page: filters?.page,
      limit: filters?.limit,
    }

    if (isSearch) {
      params.query = this.buildSearchQuery(filters?.search, filters?.tag)
    } else if (filters?.category) {
      params.category = filters.category
    }

    const response = await this.httpClient.get<ApiResponse<ArticleDTO[]>>(endpoint, { params })
    const rawData = response.data.data ?? []

    return rawData.map((dto) => this.mapToArticle(dto))
  }

  async getArticlesCount(locale: string, filters?: ArticlesFilters): Promise<number> {
    const params: ArticleQueryParams = {
      language_code: locale,
      category: filters?.category,
    }

    const response = await this.httpClient.get<ApiResponse<CountResponse>>('/g/articles/count', {
      params,
    })
    return response.data.data.count
  }

  async getArticleById(id: string, locale: string): Promise<Article> {
    const params: ArticleQueryParams = {
      article_id: id,
      language_code: locale,
    }

    const response = await this.httpClient.get<ApiResponse<ArticleDTO>>('/g/article/detailed', {
      params,
    })
    return this.mapToArticle(response.data.data)
  }

  async getRelatedArticles(
    articleId: string,
    locale: string,
    limit: number = 4,
  ): Promise<Article[]> {
    // Fallback: since there's no dedicated endpoint yet, request the list instead
    return this.getArticles(locale, { limit })
  }

  async getAllCategories(): Promise<string[]> {
    return [] // TODO: no dedicated endpoint yet
  }

  async getAllTags(): Promise<string[]> {
    return [] // TODO: no dedicated endpoint yet
  }
}
