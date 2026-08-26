// Wrapper for the standard Go response (gin.H)
export interface ApiResponse<T> {
  status: string
  message: string
  data: T
}

// Response for the /g/articles/count endpoint
export interface CountResponse {
  count: number
}

// Strict filters for calling repository and store methods
export interface ArticlesFilters {
  category?: string
  tag?: string | string[]
  search?: string
  page?: number
  limit?: number
}

// Strict mapping of query params for Axios (matches ArticleWebQuery in Go)
export interface ArticleQueryParams {
  language_code: string
  page?: number
  limit?: number
  query?: string
  category?: string
  article_id?: string
}

// Data Transfer Object: what actually comes from the backend (snake_case and stringified JSON)
export interface ArticleDTO {
  id: string
  title: string
  publishedDate: string
  category: string
  tags: string
  content: string
  language_code: string
  image_source: string
  source_link?: string
  neural_networks?: Record<string, unknown>
}

// Clean model for the UI and Pinia (camelCase, proper types)
export interface Article {
  id: string
  title: string
  publishedDate: string
  category: string
  tags: string[]
  content: string
  languageCode: string
  imageSource: string
  sourceLink?: string
  neuralNetworks?: Record<string, unknown>
}
