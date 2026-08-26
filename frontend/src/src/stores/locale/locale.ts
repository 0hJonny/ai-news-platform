import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { type LocaleCode, AVAILABLE_LOCALES, DEFAULT_LOCALE } from '@/locales/locales'

export const useLocaleStore = defineStore('locale', () => {
  const currentCode = ref<LocaleCode>(DEFAULT_LOCALE)

  const currentLocale = computed(() => AVAILABLE_LOCALES.find((l) => l.code === currentCode.value))

  function setLocale(code: LocaleCode) {
    if (code === currentCode.value) return

    currentCode.value = code
    localStorage.setItem('locale', code)

    if (typeof document !== 'undefined') {
      document.documentElement.lang = code
    }
  }

  return {
    currentCode,
    currentLocale,
    setLocale,
    AVAILABLE_LOCALES,
  }
})
