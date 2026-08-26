import { watch } from 'vue'
import { i18n } from '@/plugins/i18n'
import { useLocaleStore } from '@/stores/locale/locale'
import type { LocaleCode } from '@/locales/locales'

export function setupLocaleSync() {
  const localeStore = useLocaleStore()

  localeStore.currentCode = i18n.global.locale.value as LocaleCode

  watch(
    () => localeStore.currentCode,
    (newLocale) => {
      i18n.global.locale.value = newLocale
    },
    { immediate: true },
  )

  if (typeof window !== 'undefined') {
    window.addEventListener('storage', (e) => {
      if (e.key === 'locale' && e.newValue) {
        localeStore.setLocale(e.newValue as LocaleCode)
      }
    })
  }
}
