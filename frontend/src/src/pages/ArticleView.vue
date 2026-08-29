<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useArticlesStore } from '@/stores/article/articles'
import ArticleTag from '@/components/features/article/ArticleTag.vue'
import { useLocaleStore } from '@/stores/locale/locale'
import { renderMarkdown } from '@/utils/markdown'

const route = useRoute()
const router = useRouter()

const localeStore = useLocaleStore()
const articlesStore = useArticlesStore()

const locale = computed(() => localeStore.currentCode)
const articleId = computed(() => route.params.id as string)

onMounted(async () => {
  await articlesStore.fetchArticles(locale.value)
})

watch(locale, async () => {
  await articlesStore.fetchArticles(locale.value)
})

const article = computed(() => articlesStore.getArticleById(articleId.value))

const markdownToHtml = computed(() => {
  const html = article.value?.content ? renderMarkdown(article.value.content) : ''
  return article.value ? html : ''
})

const formattedDate = computed(() => {
  if (!article.value) return ''
  const date = new Date(article.value.publishedDate)
  return date.toLocaleDateString(locale.value, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})

const goBack = () => {
  router.back()
}
</script>

<template>
  <div v-if="article" class="article-view">
    <div class="article-view__container">
      <!-- Back button -->
      <button @click="goBack" class="article-view__back-button">
        <img
          src="/arrow-left.svg"
          :alt="$t('article.backAlt')"
          class="w-5 h-5 invert dark:invert-0"
        />
        <span>{{ $t('article.back') }}</span>
      </button>

      <!-- Header -->
      <header class="article-view__header">
        <div class="article-view__meta">
          <span class="article-view__category">{{ article.category }}</span>
          <span class="article-view__separator">•</span>
          <span class="article-view__date">{{ formattedDate }}</span>
        </div>

        <h1 class="article-view__title">{{ article.title }}</h1>

        <!-- Tags -->
        <div class="article-view__tags">
          <ArticleTag v-for="(tag, index) in article.tags" :key="index" :tag="tag" />
        </div>
      </header>

      <!-- Image -->
      <div class="article-view__image-wrapper">
        <img :src="article.imageSource" :alt="article.title" class="article-view__image" />
      </div>

      <!-- Content -->
      <article
        class="article-view__content prose dark:prose-invert max-w-none"
        v-html="markdownToHtml"
      />
    </div>
  </div>

  <!-- Article not found -->
  <div v-else class="article-view__not-found">
    <h2 class="text-3xl font-bold mb-4">{{ $t('article.notFound') }}</h2>
    <button @click="goBack" class="article-view__back-button">
      {{ $t('article.goBack') }}
    </button>
  </div>
</template>

<style scoped>
.article-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.article-view__container {
  background: var(--color-bkg);
  border-radius: 1rem;
  overflow: hidden;
}

.article-view__back-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  margin-bottom: 2rem;
  background: transparent;
  border: 1px solid var(--color-palette-silver);
  border-radius: 0.5rem;
  color: var(--color-text-primary);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.article-view__back-button:hover {
  background: var(--color-palette-silver);
  transform: translateX(-4px);
}

.article-view__header {
  padding: 2rem 0;
}

.article-view__meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-title);
  margin-bottom: 1rem;
}

.article-view__category {
  text-transform: capitalize;
}

.article-view__separator {
  color: var(--color-text-sub);
}

.article-view__date {
  color: var(--color-text-sub);
}

.article-view__title {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-text-primary);
  margin-bottom: 1.5rem;
}

.article-view__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.article-view__image-wrapper {
  margin: 2rem 0;
  border-radius: 1rem;
  overflow: hidden;
}

.article-view__image {
  width: 100%;
  height: auto;
  display: block;
}

.article-view__content {
  padding: 2rem 0;
  color: var(--color-text-primary);
  line-height: 1.8;
}

.article-view__content :deep(h3) {
  color: var(--color-text-title);
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.article-view__content :deep(p) {
  margin-bottom: 1rem;
  color: var(--color-text-primary);
}

.article-view__content :deep(ul) {
  list-style: disc;
  padding-left: 2rem;
  margin-bottom: 1rem;
}

.article-view__content :deep(li) {
  margin-bottom: 0.5rem;
}

.article-view__not-found {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--color-text-primary);
}

@media (max-width: 768px) {
  .article-view__title {
    font-size: 1.875rem;
  }
}
</style>
