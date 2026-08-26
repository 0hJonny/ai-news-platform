import type { Article, ArticlesFilters } from '@/types/article/article'
import type { IArticlesRepository } from './IArticlesRepository'
import { mockArticles } from '@/stores/article/mock/articles'

export class MockArticlesRepository implements IArticlesRepository {
  getArticlesCount(locale: string, filters?: ArticlesFilters): Promise<number> {
    throw new Error('Method not implemented.')
  }
  private readonly mockDelay: number = 300
  private readonly imageBaseUrl: string = '/'

  private simulateDelay(ms: number = this.mockDelay): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  private normalizeImageUrl(imageSource: string): string {
    if (imageSource.startsWith('http://') || imageSource.startsWith('https://')) {
      return imageSource
    }
    return `${this.imageBaseUrl}${imageSource}`
  }

  private processArticle(article: Article): Article {
    return {
      ...article,
      imageSource: this.normalizeImageUrl(article.imageSource),
    }
  }

  async getArticles(locale: string, filters?: ArticlesFilters): Promise<Article[]> {
    await this.simulateDelay()

    let filtered = mockArticles.filter((article) => article.languageCode === locale)

    if (filters?.category) {
      filtered = filtered.filter((article) => article.category === filters.category)
    }

    if (filters?.tag) {
      filtered = filtered.filter((article) =>
        article.tags.some((tag) => tag.toLowerCase() === filters.tag!.toLowerCase()),
      )
    }

    if (filters?.search) {
      const searchLower = filters.search.toLowerCase()
      filtered = filtered.filter(
        (article) =>
          article.title.toLowerCase().includes(searchLower) ||
          article.content.toLowerCase().includes(searchLower) ||
          article.tags.some((tag) => tag.toLowerCase().includes(searchLower)),
      )
    }

    filtered.sort((a, b) => {
      return new Date(b.publishedDate).getTime() - new Date(a.publishedDate).getTime()
    })

    return filtered.map((article) => this.processArticle(article))
  }

  async getArticleById(id: string, locale: string): Promise<Article> {
    await this.simulateDelay()

    const article = mockArticles.find(
      (article) => article.id === id && article.languageCode === locale,
    )

    if (!article) {
      throw new Error(`Article with id "${id}" and locale "${locale}" not found`)
    }

    return this.processArticle(article)
  }

  async getArticlesByCategory(category: string, locale: string): Promise<Article[]> {
    await this.simulateDelay()

    const filtered = mockArticles.filter(
      (article) => article.category === category && article.languageCode === locale,
    )

    return filtered.map((article) => this.processArticle(article))
  }

  async getArticlesByTag(tag: string, locale: string): Promise<Article[]> {
    await this.simulateDelay()

    const filtered = mockArticles.filter(
      (article) =>
        article.tags.some((t) => t.toLowerCase() === tag.toLowerCase()) &&
        article.languageCode === locale,
    )

    return filtered.map((article) => this.processArticle(article))
  }

  async getRelatedArticles(
    articleId: string,
    locale: string,
    limit: number = 4,
  ): Promise<Article[]> {
    await this.simulateDelay()

    const currentArticle = mockArticles.find(
      (article) => article.id === articleId && article.languageCode === locale,
    )

    if (!currentArticle) {
      return []
    }

    // Find articles with similar tags or the same category
    const related = mockArticles.filter((article) => {
      // Exclude the current article and articles in other languages
      if (article.id === articleId || article.languageCode !== locale) {
        return false
      }

      // Check for shared tags
      const hasCommonTags = article.tags.some((tag) => currentArticle.tags.includes(tag))
      const sameCategory = article.category === currentArticle.category

      return hasCommonTags || sameCategory
    })

    // Sort by relevance (number of shared tags)
    related.sort((a, b) => {
      const aCommonTags = a.tags.filter((tag) => currentArticle.tags.includes(tag)).length
      const bCommonTags = b.tags.filter((tag) => currentArticle.tags.includes(tag)).length

      // First by number of shared tags
      if (bCommonTags !== aCommonTags) {
        return bCommonTags - aCommonTags
      }

      // Then by publish date
      return new Date(b.publishedDate).getTime() - new Date(a.publishedDate).getTime()
    })

    return related.slice(0, limit).map((article) => this.processArticle(article))
  }

  async getAllCategories(locale: string): Promise<string[]> {
    await this.simulateDelay(100)

    const categories = new Set(
      mockArticles
        .filter((article) => article.languageCode === locale)
        .map((article) => article.category),
    )

    return Array.from(categories).sort()
  }

  async getAllTags(locale: string): Promise<string[]> {
    await this.simulateDelay(100)

    const tagsSet = new Set<string>()

    mockArticles
      .filter((article) => article.languageCode === locale)
      .forEach((article) => {
        article.tags.forEach((tag) => tagsSet.add(tag))
      })

    return Array.from(tagsSet).sort()
  }
}
