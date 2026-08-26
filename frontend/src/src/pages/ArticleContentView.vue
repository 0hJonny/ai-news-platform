<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { useArticle } from '@/composables/useArticle'
import ArticleTag from '@/components/features/article/ArticleTag.vue'
import { formatDate, formatRelativeTime } from '@/utils/dateFormatter.ts'
import { useLocaleStore } from '@/stores/locale/locale'
import { renderMarkdown } from '@/utils/markdown'

// Lazy loading for recommendations
const ArticlesList = defineAsyncComponent(
  () => import('@/components/features/article/ArticlesListPage.vue'),
)

const localeStore = useLocaleStore()
const locale = computed(() => localeStore.currentCode)

const { currentArticle, articleLoading, error } = useArticle()

const formattedDate = computed(() => {
  if (!currentArticle.value) return ''
  return formatDate(currentArticle.value.publishedDate, locale.value)
})

const relativeTime = computed(() => {
  if (!currentArticle.value) return ''
  return formatRelativeTime(currentArticle.value.publishedDate, locale.value)
})

// Memoize markdown parsing
const markdownToHtml = computed(() => {
  if (!currentArticle.value?.content) return ''
  return renderMarkdown(currentArticle.value.content)
})

// Memoize neural network entries + strict typing (fixes a TS error)
const neuralNetworksEntries = computed(() => {
  const nn = currentArticle.value?.neuralNetworks
  if (!nn) return []

  return Object.entries(nn).filter(
    ([, value]) => typeof value === 'string' && value.trim() !== '',
  ) as [string, string][] // Explicitly state the output is an array of string pairs
})

// Check whether there's at least one badge to display
const hasBadges = computed(() => {
  const hasNeuralNetworks = neuralNetworksEntries.value.length > 0
  const hasSourceLink = !!currentArticle.value?.sourceLink?.trim()

  return hasNeuralNetworks || hasSourceLink
})
</script>

<template>
  <div class="page-wrapper">
    <div v-if="articleLoading" class="container">
      <div class="content">
        <aside class="sidebar">
          <div class="skeleton-box"></div>
          <div class="skeleton-card"></div>
          <div class="skeleton-card"></div>
        </aside>

        <div class="article">
          <div class="skeleton-meta"></div>
          <div class="skeleton-title"></div>
          <div class="skeleton-image"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </div>
      </div>
    </div>

    <div v-else-if="error" class="container">
      <div class="error-container">
        <div class="error-icon">⚠️</div>
        <h2 class="error-title">{{ $t('article.error.title') }}</h2>
        <p class="error-message">{{ error }}</p>
        <button class="error-btn" @click="$router.back()">Go back...</button>
      </div>
    </div>

    <div v-else-if="currentArticle" class="container">
      <div class="content">
        <aside class="sidebar">
          <h4 class="sidebar-title">{{ $t('article.recommendations') }}</h4>
          <Suspense>
            <template #default>
              <ArticlesList :sideBar="true" :ignoreArticle="currentArticle.id" :limit="4" />
            </template>
            <template #fallback>
              <div class="loading-placeholder">{{ $t('article.loading') }}</div>
            </template>
          </Suspense>
        </aside>

        <article class="article">
          <div class="article-meta">
            <time class="article-date" :datetime="currentArticle.publishedDate">
              {{ formattedDate }}
              <span class="article-date-relative">· {{ relativeTime }}</span>
            </time>
            <span class="article-category">
              {{ $t(`category.${currentArticle.category}`) }}
            </span>
          </div>

          <h1 class="article-title">{{ currentArticle.title }}</h1>

          <div v-if="hasBadges" class="article-meta-row">
            <div v-if="neuralNetworksEntries.length" class="meta-group">
              <span class="meta-label">{{ $t('article.processedBy') }}:</span>
              <div class="meta-tags-list">
                <div v-for="[key, tag] in neuralNetworksEntries" :key="key" class="badge-item">
                  <div class="badge-tooltip">
                    {{ key.charAt(0).toUpperCase() + key.slice(1) }}
                  </div>
                  <ArticleTag :tag="tag" />
                </div>
              </div>
            </div>

            <div
              v-if="neuralNetworksEntries.length && currentArticle.sourceLink?.trim()"
              class="meta-divider"
            ></div>

            <a
              v-if="currentArticle.sourceLink?.trim()"
              :href="currentArticle.sourceLink"
              class="source-link-compact"
              target="_blank"
              rel="noopener noreferrer"
            >
              <svg class="source-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path
                  d="M12 8.66667V12.6667C12 13.0203 11.8595 13.3594 11.6095 13.6095C11.3594 13.8595 11.0203 14 10.6667 14H3.33333C2.97971 14 2.64057 13.8595 2.39052 13.6095C2.14048 13.3594 2 13.0203 2 12.6667V5.33333C2 4.97971 2.14048 4.64057 2.39052 4.39052C2.64057 4.14048 2.97971 4 3.33333 4H7.33333"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M10 2H14V6"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M6.66667 9.33333L14 2"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <span>{{ $t('article.viewSource') }}</span>
            </a>
          </div>

          <figure class="article-figure">
            <img
              :src="currentArticle.imageSource"
              :alt="currentArticle.title"
              class="article-image"
              loading="lazy"
              decoding="async"
            />
          </figure>

          <div class="article-content markdown-body" v-html="markdownToHtml" />

          <nav v-if="currentArticle.tags.length" class="article-tags">
            <span class="tags-label">{{ $t('article.tags') }}:</span>
            <div class="tags-list">
              <router-link
                v-for="tag in currentArticle.tags"
                :key="tag"
                :to="`/search?tag=${tag}`"
                class="tag-link"
              >
                <ArticleTag :tag="tag" />
              </router-link>
            </div>
          </nav>
        </article>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* =========================================
   Layout & Grid
   ========================================= */
.page-wrapper {
  min-height: 100vh;
  background: var(--color-bkg);
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-l);
}

.content {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: calc(var(--space-l) + var(--space-m));
  align-items: start;
}

@media (max-width: 1024px) {
  .content {
    grid-template-columns: 1fr;
  }
  .sidebar {
    order: 2;
  }
  .article {
    order: 1;
  }
}

@media (max-width: 768px) {
  .container {
    padding: var(--space-m);
  }
}

/* =========================================
   Sidebar
   ========================================= */
.sidebar {
  position: sticky;
  top: var(--space-l);
}

.sidebar-title {
  margin: 0 0 var(--space-m) 0;
  color: var(--color-text-primary);
  font-size: 18px;
  font-weight: 600;
}

.loading-placeholder {
  padding: var(--space-m);
  text-align: center;
  color: var(--color-text-sub);
  font-size: var(--font-size-small);
}

/* =========================================
   Article Main Blocks
   ========================================= */
.article {
  max-width: 800px;
}

.article-meta {
  display: flex;
  align-items: center;
  gap: var(--space-m);
  margin-bottom: var(--space-s);
  flex-wrap: wrap;
}

.article-date {
  color: var(--color-text-sub);
  font-size: var(--font-size-small);
  font-weight: 500;
}

.article-date-relative {
  color: var(--color-palette-silver);
}

.article-category {
  padding: var(--space-xs) var(--space-n);
  background: var(--color-text-title);
  color: var(--color-bkg);
  border-radius: 16px;
  font-size: var(--font-size-tiny);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.article-title {
  margin: 0 0 var(--space-m) 0;
  color: var(--color-text-primary);
  font-size: clamp(28px, 5vw, 42px);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.article-figure {
  margin: 0 0 var(--space-l) 0;
}

.article-image {
  width: 100%;
  height: auto;
  border-radius: var(--space-n);
  box-shadow: 0 4px 20px var(--color-divider-light);
  transition: transform 0.3s ease;
}

.article-image:hover {
  transform: scale(1.01);
}

/* =========================================
   ✨ Compact Meta Row (AI & Source)
   ========================================= */
.article-meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-m);
  margin-bottom: var(--space-l);
}

.meta-group {
  display: flex;
  align-items: center;
  gap: var(--space-s);
  flex-wrap: wrap;
}

.meta-label {
  color: var(--color-text-sub);
  font-size: var(--font-size-small);
  font-weight: 500;
}

.meta-tags-list {
  display: flex;
  gap: var(--space-s);
  flex-wrap: wrap;
}

/* Original tooltip */
.badge-item {
  position: relative;
  cursor: pointer;
}

.badge-tooltip {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 8px;
  background: var(--color-text-title);
  color: var(--color-bkg);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Small triangle for the tooltip */
.badge-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-width: 4px;
  border-style: solid;
  border-color: var(--color-text-title) transparent transparent transparent;
}

.badge-item:hover .badge-tooltip {
  opacity: 1;
  visibility: visible;
  bottom: calc(100% + 8px); /* Slight upward shift on appearance */
}

/* Divider between the AI tags and the Source button */
.meta-divider {
  width: 1px;
  height: 16px;
  background: var(--color-border);
}

/* Source Link */
.source-link-compact {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: var(--font-size-small);
  font-weight: 500;
  color: var(--color-text-primary);
  text-decoration: none;
  background: var(--color-bkg-soft);
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
}

.source-link-compact:hover {
  background: var(--color-text-title);
  border-color: var(--color-text-title);
  color: var(--color-bkg);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* =========================================
   Markdown / Article Content Styles
   ========================================= */
.article-content {
  color: var(--color-text-primary);
  font-size: 17px;
  line-height: 1.75;
  word-wrap: break-word;
  margin-bottom: var(--space-xl);
}

.article-content :deep(h1),
.article-content :deep(h2),
.article-content :deep(h3),
.article-content :deep(h4),
.article-content :deep(h5),
.article-content :deep(h6) {
  color: var(--color-text-primary);
  margin-top: 1.8em;
  margin-bottom: 0.8em;
  font-weight: 600;
  line-height: 1.3;
}

.article-content :deep(h2) {
  font-size: 1.75em;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.4em;
}

.article-content :deep(h3) {
  font-size: 1.4em;
}
.article-content :deep(h4) {
  font-size: 1.2em;
}
.article-content :deep(p) {
  margin-top: 0;
  margin-bottom: 1.25em;
}

.article-content :deep(a) {
  color: #4285f4;
  text-decoration: none;
  font-weight: 500;
  border-bottom: 1px solid transparent;
  transition: all 0.2s ease;
}
.article-content :deep(a:hover) {
  border-bottom-color: #4285f4;
  opacity: 0.8;
}

.article-content :deep(blockquote) {
  margin: 1.5em 0;
  padding: 0.8em 1.2em;
  color: var(--color-text-sub);
  background: var(--color-bkg-soft);
  border-left: 4px solid #9b72cb;
  border-radius: 0 12px 12px 0;
  font-style: italic;
}

.article-content :deep(ul),
.article-content :deep(ol) {
  margin-top: 0;
  margin-bottom: 1.25em;
  padding-left: 1.5em;
}
.article-content :deep(li) {
  margin-bottom: 0.4em;
}
.article-content :deep(li::marker) {
  color: #9b72cb;
  font-weight: bold;
}

.article-content :deep(code:not(pre code)) {
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 0.85em;
  background-color: var(--color-bkg-mute);
  padding: 0.2em 0.4em;
  border-radius: 6px;
  color: #d23669;
  word-break: break-word;
}

.article-content :deep(pre) {
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 0.9em;
  background-color: #1e1e2e;
  color: #cdd6f4;
  padding: 1.25em;
  border-radius: 12px;
  overflow-x: auto;
  margin: 1.5em 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.article-content :deep(pre::-webkit-scrollbar) {
  height: 8px;
}
.article-content :deep(pre::-webkit-scrollbar-thumb) {
  background: #45475a;
  border-radius: 4px;
}
.article-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: inherit;
  border-radius: 0;
}

.article-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
  font-size: 0.95em;
  overflow-x: auto;
  display: block;
}
.article-content :deep(th),
.article-content :deep(td) {
  padding: 0.75em 1em;
  border: 1px solid var(--color-border);
  text-align: left;
}
.article-content :deep(th) {
  background-color: var(--color-bkg-soft);
  font-weight: 600;
  color: var(--color-text-primary);
}
.article-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 12px;
  margin: 1.5em 0;
  display: block;
}
.article-content :deep(hr) {
  height: 1px;
  background-color: var(--color-border);
  border: none;
  margin: 2.5em 0;
}

/* =========================================
   Post-Content Tags
   ========================================= */
.article-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-n);
  padding: var(--space-m) 0;
  border-top: 1px solid var(--color-border);
}
.tags-label {
  color: var(--color-text-sub);
  font-size: var(--font-size-small);
  font-weight: 600;
}
.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-s);
}
.tag-link {
  text-decoration: none;
  transition: transform 0.2s;
}
.tag-link:hover {
  transform: translateY(-2px);
}

/* =========================================
   Skeletons
   ========================================= */
.skeleton-box,
.skeleton-card,
.skeleton-meta,
.skeleton-title,
.skeleton-image,
.skeleton-line {
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

.skeleton-box {
  height: 24px;
  width: 120px;
  margin-bottom: var(--space-m);
}
.skeleton-card {
  height: 180px;
  margin-bottom: var(--space-m);
}
.skeleton-meta {
  height: 20px;
  width: 200px;
  margin-bottom: var(--space-m);
}
.skeleton-title {
  height: 48px;
  width: 100%;
  margin-bottom: var(--space-l);
}
.skeleton-image {
  height: 400px;
  width: 100%;
  margin-bottom: var(--space-l);
}
.skeleton-line {
  height: 20px;
  width: 100%;
  margin-bottom: var(--space-m);
}
.skeleton-line.short {
  width: 70%;
}

/* =========================================
   Error
   ========================================= */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: var(--space-l);
}
.error-icon {
  font-size: 64px;
  margin-bottom: var(--space-m);
}
.error-title {
  margin: 0 0 var(--space-m) 0;
  color: var(--color-text-primary);
  font-size: 32px;
  font-weight: 700;
}
.error-message {
  margin: 0 0 var(--space-m) 0;
  color: var(--color-text-sub);
  font-size: 18px;
  max-width: 600px;
}
.error-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bkg-soft);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: 0.2s;
}
.error-btn:hover {
  background: var(--color-bkg-mute);
}
</style>
