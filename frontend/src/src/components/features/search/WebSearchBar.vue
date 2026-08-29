<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useSearchStore } from '@/stores/search/search'
import { storeToRefs } from 'pinia'
import ArticleTag from '@/components/features/article/ArticleTag.vue'
import { useLocaleStore } from '@/stores/locale/locale'

const localeStore = useLocaleStore()
const searchStore = useSearchStore()

const locale = computed(() => localeStore.currentCode)
const { searchTags } = storeToRefs(searchStore)

const inputValue = ref('')
const isFocused = ref(false)

// Main search function
const handleSearch = async () => {
  searchStore.setSearchQuery(inputValue.value)
  await searchStore.search(locale.value)
}

const handleKeyup = (event: KeyboardEvent) => {
  // Add a tag when space is pressed, if it starts with #
  if (event.key === ' ' && inputValue.value.trim().startsWith('#')) {
    searchStore.addTag(inputValue.value.trim())
    inputValue.value = ''
    handleSearch() // 👈 Run the search after adding the tag
  }

  // Search on Enter
  if (event.key === 'Enter') {
    handleSearch()
  }
}

const handleDelete = () => {
  // Remove the last tag on Backspace when the field is empty
  if (inputValue.value === '' && searchTags.value.length > 0) {
    searchStore.removeTag(searchTags.value.length - 1)
    handleSearch() // 👈 Run the search after removing the tag
  }
}

const removeTag = (index: number) => {
  searchStore.removeTag(index)
  handleSearch() // 👈 Run the search after removing the tag by click
}

const clearAll = () => {
  inputValue.value = ''
  searchStore.clearSearch() // The store resets, UI goes back to "Start searching..."
}

// Auto-search when the language changes
watch(locale, () => {
  if (searchStore.hasQuery) {
    handleSearch()
  }
})
</script>

<template>
  <div class="search-bar" :class="{ 'search-bar--focused': isFocused }">
    <div class="search-bar__input-wrapper">
      <div v-for="(tag, index) in searchTags" :key="tag" class="search-bar__tag">
        <ArticleTag :tag="tag.replace('#', '')" @click="removeTag(index)" />
      </div>

      <input
        v-model="inputValue"
        @focus="isFocused = true"
        @blur="isFocused = false"
        @keyup="handleKeyup"
        @keydown.delete="handleDelete"
        :placeholder="$t('search.placeholder')"
        class="search-bar__input"
      />
    </div>

    <div class="search-bar__actions">
      <button
        v-if="inputValue || searchTags.length > 0"
        class="search-bar__clear"
        @click="clearAll"
        :aria-label="$t('search.clear')"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
      <button
        @click="handleSearch"
        class="search-bar__submit"
        :disabled="!inputValue && searchTags.length === 0"
      >
        {{ $t('search.searchButton') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border: 2px solid var(--color-palette-silver);
  border-radius: 0.75rem;
  background: var(--color-bkg);
  transition: all 0.3s ease;
}

.search-bar--focused {
  border-color: var(--color-text-title);
  box-shadow: 0 0 0 3px rgba(105, 65, 198, 0.1);
}

.search-bar__input-wrapper {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  flex: 1;
  min-width: 0;
}

.search-bar__tag {
  cursor: pointer;
}

.search-bar__input {
  flex: 1;
  min-width: 200px;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-text-primary);
  font-size: 1rem;
  padding: 0.5rem;
}

.search-bar__input::placeholder {
  color: var(--color-text-sub);
}

.search-bar__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.search-bar__clear {
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--color-text-primary);
  padding: 0.25rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.search-bar__clear:hover {
  opacity: 1;
}

.search-bar__submit {
  border: none;
  background: var(--color-text-title);
  color: white;
  padding: 0.625rem 1.5rem;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
  white-space: nowrap;
}

.search-bar__submit:hover:not(:disabled) {
  background-color: #7c3aed;
}

.search-bar__submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .search-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-bar__actions {
    justify-content: flex-end;
  }

  .search-bar__input {
    min-width: 100%;
  }
}
</style>
