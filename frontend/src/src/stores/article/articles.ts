import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Article, ArticlesFilters } from '@/types/article/article'
import { articlesRepository } from '@/services/articles'

interface ArticleCache {
  [key: string]: {
    data: Article
    timestamp: number
  }
}

const CACHE_DURATION = 5 * 60 * 1000

export const useArticlesStore = defineStore('articles', () => {
  const articlesList = ref<Article[]>([])
  const currentArticle = ref<Article | null>(null)
  const articleCache = ref<ArticleCache>({})

  const loading = ref<boolean>(false)
  const articleLoading = ref<boolean>(false)
  const error = ref<string | null>(null)

  const totalItems = ref<number>(0)
  const currentPage = ref<number>(1)
  const elementsPerPage = ref<number>(12)
  const currentFilters = ref<ArticlesFilters>({})
  const currentLocale = ref<string>('')

  const totalPages = computed<number>(() => Math.ceil(totalItems.value / elementsPerPage.value))

  const isCacheValid = (cacheKey: string): boolean => {
    const cached = articleCache.value[cacheKey]
    return Boolean(cached && Date.now() - cached.timestamp < CACHE_DURATION)
  }

  const getCacheKey = (id: string, locale: string): string => `${id}_${locale}`

  const fetchArticles = async (
    locale: string,
    filters?: ArticlesFilters,
    loadCount: boolean = true,
  ): Promise<void> => {
    loading.value = true
    error.value = null

    currentLocale.value = locale

    if (filters) {
      currentFilters.value = { ...filters }
    }

    const requestFilters: ArticlesFilters = {
      page: currentPage.value,
      limit: elementsPerPage.value,
      ...currentFilters.value,
    }

    try {
      const [articlesData, countData] = await Promise.all([
        articlesRepository.getArticles(locale, requestFilters),
        loadCount && !requestFilters.search
          ? articlesRepository.getArticlesCount(locale, requestFilters)
          : Promise.resolve(totalItems.value),
      ])

      articlesList.value = articlesData

      if (loadCount) {
        totalItems.value = countData
      }
    } catch (err: unknown) {
      error.value =
        err instanceof Error ? err.message : 'An unexpected error occurred while fetching articles'
      console.error(err)
      articlesList.value = []
    } finally {
      loading.value = false
    }
  }

  const fetchArticleById = async (id: string, locale: string): Promise<Article | null> => {
    const cacheKey = getCacheKey(id, locale)

    if (isCacheValid(cacheKey)) {
      const cachedData = articleCache.value[cacheKey]?.data
      if (cachedData) {
        currentArticle.value = cachedData
        return currentArticle.value
      }
    }

    articleLoading.value = true
    error.value = null

    try {
      const article = await articlesRepository.getArticleById(id, locale)
      currentArticle.value = article

      articleCache.value[cacheKey] = { data: article, timestamp: Date.now() }
      return article
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Article not found'
      currentArticle.value = null
      throw err
    } finally {
      articleLoading.value = false
    }
  }

  const setPage = async (page: number): Promise<void> => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
      await fetchArticles(currentLocale.value, currentFilters.value, false)
    }
  }

  const resetPagination = (): void => {
    currentPage.value = 1
  }

  const getArticleById = (id: string): Article | undefined => {
    return articlesList.value.find((article) => article.id === id)
  }

  const clearCurrentArticle = (): void => {
    currentArticle.value = null
  }

  const clearCache = (): void => {
    articleCache.value = {}
  }

  const $reset = (): void => {
    articlesList.value = []
    currentArticle.value = null
    articleCache.value = {}
    currentFilters.value = {}
    currentLocale.value = ''
    loading.value = false
    articleLoading.value = false
    error.value = null
    currentPage.value = 1
    totalItems.value = 0
  }

  return {
    articles: computed(() => articlesList.value),
    currentArticle: computed(() => currentArticle.value),
    loading: computed(() => loading.value),
    articleLoading: computed(() => articleLoading.value),
    error: computed(() => error.value),
    currentPage,
    elementsPerPage,
    totalItems,
    totalPages,
    fetchArticles,
    fetchArticleById,
    setPage,
    resetPagination,
    getArticleById,
    clearCurrentArticle,
    clearCache,
    $reset,
  }
})
