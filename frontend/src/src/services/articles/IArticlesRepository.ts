import type { Article, ArticlesFilters } from '@/types/article/article'

export interface IArticlesRepository {
  getArticles(locale: string, filters?: ArticlesFilters): Promise<Article[]>
  getArticlesCount(locale: string, filters?: ArticlesFilters): Promise<number>
  getArticleById(id: string, locale: string): Promise<Article>
  getRelatedArticles(articleId: string, locale: string, limit?: number): Promise<Article[]>
  getAllCategories(locale: string): Promise<string[]>
  getAllTags(locale: string): Promise<string[]>
}
