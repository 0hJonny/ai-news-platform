<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { useArticlesStore } from '@/stores/article/articles'
import ArticlesListPage from '@/components/features/article/ArticlesListPage.vue'
import Pagination from '@/components/shared/PaginationBar.vue'

const props = defineProps<{
  category: string
}>()

const { t, te } = useI18n()
const articlesStore = useArticlesStore()
const { currentPage, totalPages, loading } = storeToRefs(articlesStore)

const handlePageChange = (page: number) => {
  articlesStore.setPage(page)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const categoryTitle = computed(() => {
  const i18nKey = `category.${props.category}`
  return te(i18nKey) ? t(i18nKey) : props.category.charAt(0).toUpperCase() + props.category.slice(1)
})
</script>

<template>
  <div class="category-page">
    <div class="header-container mb-12 text-center">
      <h1 class="text-5xl font-bold mb-4">
        {{ categoryTitle }}
      </h1>
      <p class="text-xl text-slate-600 dark:text-slate-400">
        {{ $t('category.subtitle', { category: categoryTitle }) }}
      </p>
    </div>

    <ArticlesListPage :category="props.category" />

    <Pagination
      :current-page="currentPage"
      :total-pages="totalPages"
      :loading="loading"
      @update:current-page="handlePageChange"
    />
  </div>
</template>

<style scoped>
.category-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}
</style>
