<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useSearchStore } from '@/stores/search/search'
import ArticleCard from '@/components/features/article/ArticleCard.vue'

const searchStore = useSearchStore()
const { searchResults, loading, error, hasQuery } = storeToRefs(searchStore)
</script>

<template>
  <div class="search-results">
    <!-- Loading -->
    <div v-if="loading" class="search-results__loading">
      <p>{{ $t('search.searching') }}</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="search-results__error">
      <p>{{ error }}</p>
    </div>

    <!-- Results -->
    <div v-else-if="searchResults.length > 0" class="search-results__grid">
      <ArticleCard
        v-for="article in searchResults"
        :key="article.id"
        :article="article"
        class="article-card-body"
      />
    </div>

    <!-- No results -->
    <div v-else-if="hasQuery" class="search-results__empty">
      <h2>{{ $t('search.noResults') }}</h2>
      <p>{{ $t('search.tryDifferent') }}</p>
    </div>

    <!-- Initial state -->
    <div v-else class="search-results__initial">
      <p>{{ $t('search.startSearching') }}</p>
    </div>
  </div>
</template>

<style scoped>
.search-results__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.search-results__loading,
.search-results__error,
.search-results__empty,
.search-results__initial {
  text-align: center;
  padding: 4rem 2rem;
}

.search-results__loading p {
  font-size: 1.125rem;
  color: var(--color-text-sub);
}

.search-results__error p {
  font-size: 1.125rem;
  color: #ef4444;
}

.search-results__empty h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 0.5rem;
}

.search-results__empty p {
  color: var(--color-text-sub);
}

.search-results__initial p {
  font-size: 1.125rem;
  color: var(--color-text-sub);
}

@media (max-width: 768px) {
  .search-results__grid {
    grid-template-columns: 1fr;
  }
}
</style>
