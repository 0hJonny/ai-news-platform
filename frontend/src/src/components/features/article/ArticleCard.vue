<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import ArticleTag from './ArticleTag.vue'
import type { Article } from '@/types/article/article'
import { formatDate, formatRelativeTime } from '@/utils/dateFormatter'
import { renderMarkdown } from '@/utils/markdown'

interface Props {
  article?: Article
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  article: undefined,
  loading: false,
})

const router = useRouter()
const { t, locale } = useI18n()

const imageLoaded = ref(false)
const imageError = ref(false)

// Format the date using the utility helper
const formattedDate = computed(() => {
  if (!props.article) return ''
  return formatDate(props.article.publishedDate, locale.value)
})

const relativeTime = computed(() => {
  if (!props.article) return ''
  return formatRelativeTime(props.article.publishedDate, locale.value)
})

// Content preview (first 150 characters without HTML)
const contentPreview = computed(() => {
  if (!props.article) return ''

  const html = renderMarkdown(props.article.content) as string
  const text = html.replace(/<[^>]*>/g, '')

  return text.length > 150 ? text.substring(0, 150) + '...' : text
})

// Localized category
const localizedCategory = computed(() => {
  if (!props.article) return ''
  return t(`category.${props.article.category}`)
})

const navigateToArticle = (): void => {
  if (!props.article) return

  router.push({
    name: 'article-detail',
    params: { id: props.article.id },
  })
}

const handleImageLoad = (): void => {
  imageLoaded.value = true
}

const handleImageError = (): void => {
  imageError.value = true
  imageLoaded.value = true
}
</script>

<template>
  <!-- Skeleton Loader -->
  <div v-if="loading" class="article-card skeleton-card">
    <div class="article-card__inner">
      <div class="skeleton-image"></div>
      <div class="article-card__content">
        <div class="skeleton-meta"></div>
        <div class="skeleton-title"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line short"></div>
        <div class="skeleton-tags">
          <div class="skeleton-tag"></div>
          <div class="skeleton-tag"></div>
          <div class="skeleton-tag"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Article Card -->
  <article v-else-if="article" class="article-card">
    <div class="article-card__inner">
      <!-- Image -->
      <figure class="article-card__figure">
        <div v-if="!imageLoaded" class="image-placeholder">
          <div class="spinner"></div>
        </div>
        <img
          v-show="imageLoaded && !imageError"
          :src="article.imageSource"
          :alt="article.title"
          class="article-card__image"
          loading="lazy"
          decoding="async"
          @load="handleImageLoad"
          @error="handleImageError"
          @click="navigateToArticle"
        />
        <div v-if="imageError" class="image-error" @click="navigateToArticle">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
            <path
              d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"
              fill="currentColor"
            />
          </svg>
        </div>
      </figure>

      <!-- Content -->
      <div class="article-card__content">
        <!-- Meta -->
        <div class="article-card__meta">
          <span class="meta-category">{{ localizedCategory }}</span>
          <span class="meta-separator">•</span>
          <time class="meta-date" :datetime="article.publishedDate" :title="formattedDate">
            {{ relativeTime }}
          </time>
        </div>

        <!-- Title -->
        <div class="article-card__header" @click="navigateToArticle">
          <h2 class="article-card__title">{{ article.title }}</h2>
          <svg class="article-card__icon" width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M7 17L17 7M17 7H7M17 7V17"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>

        <!-- Description -->
        <p class="article-card__description">
          {{ contentPreview }}
        </p>

        <!-- Tags -->
        <nav class="article-card__tags" aria-label="Article tags">
          <router-link
            v-for="tag in article.tags.slice(0, 3)"
            :key="tag"
            :to="`/search?tag=${tag}`"
            class="tag-link"
          >
            <ArticleTag :tag="tag" />
          </router-link>
          <span v-if="article.tags.length > 3" class="tags-more">
            +{{ article.tags.length - 3 }}
          </span>
        </nav>
      </div>
    </div>
  </article>
</template>

<style scoped>
/* Article Card */
.article-card {
  max-width: 100%;
  height: 100%;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.article-card:hover {
  transform: translateY(-4px);
}

.article-card__inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bkg);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  transition: var(--transition);
}

.article-card:hover .article-card__inner {
  box-shadow: 0 8px 24px var(--color-divider-hover);
  border-color: var(--color-divider-hover);
}

/* Image */
.article-card__figure {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: var(--color-bkg-mute);
}

.article-card__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.article-card:hover .article-card__image {
  transform: scale(1.05);
}

.image-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bkg-mute);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-text-title);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.image-error {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bkg-mute);
  color: var(--color-text-sub);
  cursor: pointer;
  transition: var(--transition);
}

.image-error:hover {
  background: var(--color-bkg-soft);
}

/* Content */
.article-card__content {
  display: flex;
  flex-direction: column;
  gap: var(--space-n);
  padding: var(--space-m);
  flex: 1;
}

/* Meta */
.article-card__meta {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  font-size: var(--font-size-small);
  font-weight: 600;
}

.meta-category {
  color: var(--color-text-title);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.meta-separator {
  color: var(--color-text-sub);
}

.meta-date {
  color: var(--color-text-sub);
  font-weight: 500;
}

/* Header */
.article-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-n);
  cursor: pointer;
}

.article-card__title {
  flex: 1;
  margin: 0;
  font-size: clamp(18px, 2vw, 20px);
  font-weight: 600;
  line-height: 1.4;
  color: var(--color-text-primary);
  transition: color 0.2s ease;
}

.article-card__header:hover .article-card__title {
  color: var(--color-text-title);
}

.article-card__icon {
  flex-shrink: 0;
  color: var(--color-text-sub);
  transition:
    transform 0.2s ease,
    color 0.2s ease;
}

.article-card__header:hover .article-card__icon {
  transform: translate(2px, -2px);
  color: var(--color-text-title);
}

/* Description */
.article-card__description {
  margin: 0;
  font-size: var(--font-size-base);
  line-height: 1.6;
  color: var(--color-text-sub);
  display: -webkit-box;
  line-clamp: 3;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Tags */
.article-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-s);
  margin-top: auto;
}

.tag-link {
  text-decoration: none;
  transition: transform 0.2s ease;
}

.tag-link:hover {
  transform: translateY(-2px);
}

.tags-more {
  padding: var(--space-xs) var(--space-n);
  background: var(--color-bkg-mute);
  color: var(--color-text-sub);
  border-radius: 16px;
  font-size: var(--font-size-tiny);
  font-weight: 500;
}

/* Skeleton Styles */
.skeleton-card .article-card__inner {
  background: var(--color-bkg);
  border-color: var(--color-border);
}

.skeleton-image,
.skeleton-meta,
.skeleton-title,
.skeleton-line,
.skeleton-tag {
  background: linear-gradient(
    90deg,
    var(--color-bkg-mute) 25%,
    var(--color-bkg-soft) 50%,
    var(--color-bkg-mute) 75%
  );
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: var(--space-s);
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.skeleton-image {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 0;
}

.skeleton-meta {
  height: 16px;
  width: 150px;
  margin-bottom: var(--space-xs);
}

.skeleton-title {
  height: 24px;
  width: 100%;
  margin-bottom: var(--space-xs);
}

.skeleton-line {
  height: 16px;
  width: 100%;
  margin-bottom: var(--space-s);
}

.skeleton-line.short {
  width: 70%;
}

.skeleton-tags {
  display: flex;
  gap: var(--space-s);
  margin-top: auto;
}

.skeleton-tag {
  height: 24px;
  width: 80px;
  border-radius: 16px;
}

/* Responsive */
@media (max-width: 768px) {
  .article-card__content {
    padding: var(--space-m) var(--space-n);
  }

  .article-card__title {
    font-size: 18px;
  }

  .article-card__description {
    font-size: var(--font-size-regular);
  }

  .article-card__meta {
    font-size: var(--font-size-tiny);
  }
}
</style>
