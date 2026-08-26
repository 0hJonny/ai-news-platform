import type { Article } from '@/types/article/article'

export interface SearchQuery {
  text: string
  tags: string[]
}

export interface SearchFilters {
  locale: string
  category?: string
}

export interface SearchResult {
  articles: Article[]
  total: number
}

export interface SearchOptions {
  page?: number
  limit?: number
}
