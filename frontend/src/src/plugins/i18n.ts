import { createI18n } from 'vue-i18n'
import ru_RU from '@/locales/ru-RU.json'
import en_US from '@/locales/en-US.json'
import { DEFAULT_LOCALE, type LocaleCode } from '@/locales/locales'

const savedLocale =
  typeof window !== 'undefined' ? (localStorage.getItem('locale') as LocaleCode | null) : null

export const i18n = createI18n({
  legacy: false,
  locale: savedLocale || DEFAULT_LOCALE,
  fallbackLocale: 'en-US',
  messages: { 'ru-RU': ru_RU, 'en-US': en_US },
  globalInjection: true,
})

export default i18n
