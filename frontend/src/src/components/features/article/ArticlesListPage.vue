<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
import { useArticlesStore } from '@/stores/article/articles'
import ArticleCard from './ArticleCard.vue'
import type { Article } from '@/types/article/article'
import { useLocaleStore } from '@/stores/locale/locale'

interface Props {
  ignoreArticle?: string
  sideBar?: boolean
  category?: string
  limit?: number
}

const props = withDefaults(defineProps<Props>(), {
  ignoreArticle: '',
  sideBar: false,
  category: '',
  limit: 12,
})

const route = useRoute()
const localeStore = useLocaleStore()
const articlesStore = useArticlesStore()
const locale = computed(() => localeStore.currentCode)
const { articles, loading, error } = storeToRefs(articlesStore)

const filteredArticles = computed<Article[]>(() => {
  let result = articles.value

  if (props.ignoreArticle) {
    result = result.filter((article) => article.id !== props.ignoreArticle)
  }

  if (props.limit) {
    result = result.slice(0, props.limit)
  }

  return result
})

const skeletonCount = computed<number>(() => {
  return props.sideBar ? 4 : props.limit
})

const loadArticles = async (): Promise<void> => {
  await articlesStore.fetchArticles(locale.value, {
    category: props.category || undefined,
    limit: props.limit,
  })
}

onMounted(() => {
  const pageFromUrl = Number(route.query.page) || 1
  articlesStore.currentPage = pageFromUrl
  loadArticles()
})

watch(
  () => [locale.value, props.category],
  () => {
    articlesStore.resetPagination()
    loadArticles()
  },
)

watch(
  () => route.query.page,
  (newPage) => {
    const page = Number(newPage) || 1
    if (page !== articlesStore.currentPage) {
      articlesStore.currentPage = page
      loadArticles()
    }
  },
)
</script>

<template>
  <div class="articles-list">
    <div v-if="error && !loading" class="error-state">
      <div class="error-icon">⚠️</div>
      <h3 class="error-title">{{ $t('articles.error.title') }}</h3>
      <p class="error-message">{{ error }}</p>
      <button class="error-button" @click="loadArticles">
        {{ $t('articles.error.retry') }}
      </button>
    </div>

    <div
      v-else
      class="articles-grid"
      :class="{
        'articles-grid--sidebar': sideBar,
        'articles-grid--main': !sideBar,
      }"
    >
      <template v-if="loading">
        <ArticleCard v-for="n in skeletonCount" :key="`skeleton-${n}`" :loading="true" />
      </template>

      <template v-else-if="filteredArticles.length">
        <ArticleCard v-for="article in filteredArticles" :key="article.id" :article="article" />
      </template>

      <div v-else class="empty-state" :class="{ 'empty-state--sidebar': sideBar }">
        <div class="empty-icon">📭</div>
        <h3 class="empty-title">
          {{ sideBar ? $t('article.noRecommendations') : $t('article.noData') }}
        </h3>
        <p v-if="!sideBar" class="empty-description">
          {{ $t('article.noDataDescription') }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.articles-list {
  width: 100%;
}

.articles-grid {
  display: grid;
  gap: 24px;
}

.articles-grid--main {
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
}

.articles-grid--sidebar {
  grid-template-columns: 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .articles-grid--main {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.error-message {
  margin: 0 0 24px 0;
  font-size: 16px;
  color: var(--color-text-secondary);
  max-width: 400px;
}

.error-button {
  padding: 12px 24px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.error-button:hover {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-state--sidebar {
  padding: 32px 16px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 24px;
  opacity: 0.5;
}

.empty-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.empty-state--sidebar .empty-title {
  font-size: 18px;
}

.empty-description {
  margin: 0;
  font-size: 16px;
  color: var(--color-text-secondary);
  max-width: 400px;
}

@media (prefers-color-scheme: dark) {
  .error-title,
  .empty-title {
    color: var(--color-text-primary-dark);
  }

  .error-message,
  .empty-description {
    color: var(--color-text-secondary-dark);
  }
}
</style>
