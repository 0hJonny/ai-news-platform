// src/stores/search/searchStore.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Article } from '@/types/article/article'
import type { SearchQuery } from '@/types/search/search'
import { searchService } from '@/services/search' // Your factory that returns ApiSearchService

export const useSearchStore = defineStore('search', () => {
  // --- State ---
  const searchResults = ref<Article[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // Search context
  const searchQuery = ref<string>('')
  const searchTags = ref<string[]>([])
  const popularTags = ref<string[]>([])

  // Pagination and locale context
  const totalItems = ref<number>(0)
  const currentPage = ref<number>(1)
  const elementsPerPage = ref<number>(12)
  const currentLocale = ref<string>('')
  const currentCategory = ref<string | undefined>(undefined)

  // --- Getters ---
  const totalPages = computed<number>(() => Math.ceil(totalItems.value / elementsPerPage.value))

  const hasResults = computed<boolean>(() => searchResults.value.length > 0)

  const hasQuery = computed<boolean>(
    () => searchQuery.value.trim() !== '' || searchTags.value.length > 0,
  )

  const queryObj = computed<SearchQuery>(() => ({
    text: searchQuery.value,
    tags: searchTags.value,
  }))

  // --- Actions ---

  /**
   * Perform a search via the API (server-side pagination)
   */
  const executeSearch = async (locale: string, category?: string): Promise<void> => {
    loading.value = true
    error.value = null

    // Remember the context for pagination
    currentLocale.value = locale
    if (category !== undefined) {
      currentCategory.value = category
    }

    try {
      const result = await searchService.search(
        queryObj.value,
        { locale: currentLocale.value, category: currentCategory.value },
        { page: currentPage.value, limit: elementsPerPage.value },
      )

      searchResults.value = result.articles
      totalItems.value = result.total
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Search error occurred'
      console.error('[SearchStore] Error:', err)
      searchResults.value = []
      totalItems.value = 0
    } finally {
      loading.value = false
    }
  }

  /**
   * Trigger a new search (resets the page to 1)
   */
  const search = async (locale: string, category?: string): Promise<void> => {
    currentPage.value = 1
    await executeSearch(locale, category)
  }

  /**
   * Change page (uses the saved locale and category)
   */
  const setPage = async (page: number): Promise<void> => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
      await executeSearch(currentLocale.value, currentCategory.value)
    }
  }

  // --- Input state management ---

  const setSearchQuery = (text: string): void => {
    searchQuery.value = text
  }

  const addTag = (tag: string): void => {
    const cleanTag = tag.trim().replace('#', '') // Strip the hash right away
    if (cleanTag && !searchTags.value.includes(cleanTag)) {
      searchTags.value.push(cleanTag)
    }
  }

  const removeTag = (index: number): void => {
    searchTags.value.splice(index, 1)
  }

  const clearSearch = (): void => {
    searchQuery.value = ''
    searchTags.value = []
    searchResults.value = []
    currentPage.value = 1
    totalItems.value = 0
  }

  const fetchPopularTags = async (locale: string): Promise<void> => {
    try {
      popularTags.value = await searchService.getPopularTags(locale)
    } catch (err) {
      console.error('Failed to fetch popular tags:', err)
    }
  }

  return {
    // State (Readonly)
    searchResults: computed(() => searchResults.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    currentPage,
    totalPages,
    totalItems: computed(() => totalItems.value),
    searchQuery: computed(() => searchQuery.value),
    searchTags: computed(() => searchTags.value),
    popularTags: computed(() => popularTags.value),

    // Getters
    hasResults,
    hasQuery,

    // Actions
    search,
    executeSearch,
    setPage,
    fetchPopularTags,
    setSearchQuery,
    addTag,
    removeTag,
    clearSearch,
  }
})
