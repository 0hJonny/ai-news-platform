import { computed, watch, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useArticlesStore } from '@/stores/article/articles'
import { useLocaleStore } from '@/stores/locale/locale'

export function useArticle() {
  const router = useRouter()
  const route = useRoute()

  const localeStore = useLocaleStore()
  const articlesStore = useArticlesStore()

  const locale = computed(() => localeStore.currentCode)
  const { currentArticle, articleLoading, error } = storeToRefs(articlesStore)

  // Check that the id exists
  const articleId = computed(() => {
    const id = route.params.id

    // If id is an array, take the first element
    if (Array.isArray(id)) {
      return id[0]
    }

    return id as string
  })

  const loadArticle = async (): Promise<void> => {
    // Check that id exists
    if (!articleId.value) {
      console.error('Article ID is undefined')
      await router.push({ name: 'not-found' })
      return
    }

    try {
      await articlesStore.fetchArticleById(articleId.value, locale.value)

      if (currentArticle.value) {
        document.title = currentArticle.value.title
      }
    } catch (err) {
      console.error('Error loading article:', err)
      await router.push({ name: 'not-found' })
    }
  }

  // Watchers
  watch(articleId, async (newId, oldId) => {
    if (newId && newId !== oldId) {
      window.scrollTo({ top: 0, behavior: 'smooth' })
      await loadArticle()
    }
  })

  watch(locale, async () => {
    if (articleId.value) {
      await loadArticle()
    }
  })

  onMounted(async () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
    await loadArticle()
  })

  return {
    currentArticle,
    articleLoading,
    error,
    loadArticle,
  }
}
