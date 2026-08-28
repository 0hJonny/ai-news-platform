<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

interface Props {
  currentPage: number
  totalPages: number
  loading?: boolean
}

interface Emits {
  (e: 'update:currentPage', page: number): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<Emits>()

const router = useRouter()
const route = useRoute()

const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const total = props.totalPages
  const current = props.currentPage

  if (total <= 1) return []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current < 5) {
      pages.push(1, 2, 3, 4, 5, '...', total)
    } else if (current >= total - 3) {
      pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total)
    } else {
      pages.push(1, '...', current - 1, current, current + 1, '...', total)
    }
  }

  return pages
})

const changePage = (page: number | string) => {
  if (typeof page === 'number' && page !== props.currentPage && !props.loading) {
    // 1. Update the state in the parent/store
    emit('update:currentPage', page)

    // 2. Update the URL (add ?page=X)
    router.push({
      query: {
        ...route.query, // Keep the other params (e.g. tag, category)
        page: page === 1 ? undefined : page, // Clean up the URL if it's the first page (for aesthetics)
      },
    })

    // 3. Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const previousPage = () => {
  if (props.currentPage > 1 && !props.loading) {
    changePage(props.currentPage - 1)
  }
}

const nextPage = () => {
  if (props.currentPage < props.totalPages && !props.loading) {
    changePage(props.currentPage + 1)
  }
}
</script>

<template>
  <div v-if="totalPages > 1" class="pagination">
    <div class="pagination__mobile">
      <button
        @click="previousPage"
        :disabled="currentPage === 1 || loading"
        class="pagination__mobile-btn"
      >
        {{ $t('pagination.previous') }}
      </button>
      <span class="pagination__mobile-info"> {{ currentPage }} / {{ totalPages }} </span>
      <button
        @click="nextPage"
        :disabled="currentPage === totalPages || loading"
        class="pagination__mobile-btn"
      >
        {{ $t('pagination.next') }}
      </button>
    </div>

    <div class="pagination__desktop">
      <button
        @click="previousPage"
        :disabled="currentPage === 1 || loading"
        class="pagination__nav"
      >
        <svg
          class="pagination__icon"
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
            clip-rule="evenodd"
          />
        </svg>
        <span>{{ $t('pagination.previous') }}</span>
      </button>

      <div class="pagination__pages">
        <button
          v-for="(page, index) in visiblePages"
          :key="typeof page === 'number' ? page : `dots-${index}`"
          @click="changePage(page)"
          :disabled="page === '...' || page === currentPage || loading"
          class="pagination__page"
          :class="{
            'pagination__page--active': page === currentPage,
            'pagination__page--dots': page === '...',
          }"
        >
          {{ page }}
        </button>
      </div>

      <button
        @click="nextPage"
        :disabled="currentPage === totalPages || loading"
        class="pagination__nav"
      >
        <span>{{ $t('pagination.next') }}</span>
        <svg
          class="pagination__icon"
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Styles remain unchanged */
.pagination {
  width: 100%;
  margin: 2rem 0;
}

.pagination__mobile {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.pagination__mobile-btn {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-palette-silver);
  border-radius: 0.5rem;
  background: var(--color-bkg);
  color: var(--color-text-primary);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination__mobile-btn:hover:not(:disabled) {
  background: var(--color-palette-silver);
}

.pagination__mobile-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination__mobile-info {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-sub);
  white-space: nowrap;
}

.pagination__desktop {
  display: none;
}

.pagination__nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  background: none;
  color: var(--color-text-sub);
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
}

.pagination__nav:hover:not(:disabled) {
  color: var(--color-text-title);
}

.pagination__nav:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination__icon {
  width: 1.25rem;
  height: 1.25rem;
}

.pagination__pages {
  display: flex;
  gap: 0.5rem;
}

.pagination__page {
  min-width: 2.5rem;
  height: 2.5rem;
  padding: 0.5rem;
  border: none;
  border-radius: 0.5rem;
  background: transparent;
  color: var(--color-text-sub);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination__page:hover:not(:disabled):not(.pagination__page--dots) {
  background: var(--color-text-title);
  color: white;
}

.pagination__page--active {
  background: var(--color-text-title);
  color: white;
}

.pagination__page--dots {
  cursor: default;
  opacity: 0.5;
}

.pagination__page:disabled:not(.pagination__page--active) {
  cursor: default;
  opacity: 0.5;
}

@media (min-width: 640px) {
  .pagination__mobile {
    display: none;
  }

  .pagination__desktop {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
