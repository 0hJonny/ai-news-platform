export const AVAILABLE_LOCALES = [
  { code: 'ru-RU', name: 'Русский' },
  { code: 'en-US', name: 'English' },
] as const

export type LocaleCode = (typeof AVAILABLE_LOCALES)[number]['code']

export const DEFAULT_LOCALE: LocaleCode = 'ru-RU'
export const FALLBACK_LOCALE: LocaleCode = 'en-US'

export const getLocaleByCode = (code: LocaleCode) =>
  AVAILABLE_LOCALES.find((locale) => locale.code === code)
