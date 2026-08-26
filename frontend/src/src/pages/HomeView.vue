<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useArticlesStore } from '@/stores/article/articles'
import ArticlesListPage from '@/components/features/article/ArticlesListPage.vue'
import Pagination from '@/components/shared/PaginationBar.vue'

const articlesStore = useArticlesStore()
const { currentPage, totalPages, loading } = storeToRefs(articlesStore)

const handlePageChange = (page: number) => {
  articlesStore.setPage(page)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <div class="home-page">
    <div class="header-container mb-12 text-center">
      <h1 class="text-5xl font-bold mb-4">{{ $t('home.title') }}</h1>
      <p class="text-xl text-slate-600 dark:text-slate-400">
        {{ $t('home.subtitle') }}
      </p>
    </div>

    <ArticlesListPage />

    <Pagination
      v-if="totalPages > 1"
      class="mt-12"
      :current-page="currentPage"
      :total-pages="totalPages"
      :loading="loading"
      @update:current-page="handlePageChange"
    />
  </div>
</template>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 3rem 1.5rem;
}
</style>
