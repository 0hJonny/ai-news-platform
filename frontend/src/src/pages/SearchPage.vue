<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { storeToRefs } from 'pinia'
import { useSearchStore } from '@/stores/search/search'
import WebSearchBar from '@/components/features/search/WebSearchBar.vue'
import SearchResults from '@/components/features/search/SearchResults.vue'
import Pagination from '@/components/shared/PaginationBar.vue'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const searchStore = useSearchStore()
const { currentPage, totalPages, loading } = storeToRefs(searchStore)

const handlePageChange = (page: number) => {
  searchStore.setPage(page)
}

const initSearchFromUrl = () => {
  const pageFromUrl = Number(route.query.page) || 1
  searchStore.currentPage = pageFromUrl

  const routeQueryTags = route.query.tag

  if (routeQueryTags) {
    const tags = Array.isArray(routeQueryTags) ? routeQueryTags : [routeQueryTags]
    let isAdded = false

    tags.forEach((tag) => {
      if (!tag) return
      const formattedTag = `#${tag.replace('#', '')}`
      if (!searchStore.searchTags.includes(formattedTag)) {
        searchStore.addTag(formattedTag)
        isAdded = true
      }
    })

    if (isAdded || searchStore.searchResults.length === 0) {
      searchStore.executeSearch(locale.value)
    }

    const query = { ...route.query }
    delete query.tag
    router.replace({ query })
  } else if (pageFromUrl > 1) {
    searchStore.executeSearch(locale.value)
  }
}

onMounted(() => {
  document.title = t('search.title')
  initSearchFromUrl()
})

watch(
  () => route.query.tag,
  (newTag) => {
    if (newTag) {
      initSearchFromUrl()
    }
  },
)

watch(locale, () => {
  if (searchStore.hasQuery) {
    searchStore.search(locale.value)
  }
})

watch(
  () => route.query.page,
  (newPage) => {
    const page = Number(newPage) || 1
    if (page !== searchStore.currentPage && searchStore.hasQuery) {
      searchStore.currentPage = page
      searchStore.executeSearch(locale.value)
    }
  },
)

onUnmounted(() => {
  searchStore.clearSearch()
})
</script>

<template>
  <div class="search-page">
    <div class="search-page__header">
      <h1 class="search-page__title">{{ $t('search.title') }}</h1>
      <p class="search-page__subtitle">{{ $t('search.subtitle') }}</p>
    </div>

    <div class="search-page__container">
      <WebSearchBar />
      <SearchResults />

      <Pagination
        :current-page="currentPage"
        :total-pages="totalPages"
        :loading="loading"
        @update:current-page="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.search-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.search-page__header {
  margin-bottom: 3rem;
  text-align: center;
}

.search-page__title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 0.5rem;
}

.search-page__subtitle {
  font-size: 1.125rem;
  color: var(--color-text-sub);
}

.search-page__container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

@media (max-width: 768px) {
  .search-page__title {
    font-size: 2rem;
  }
}
</style>
