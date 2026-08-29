<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLocaleStore } from '@/stores/locale/locale'
import { AVAILABLE_LOCALES, type LocaleCode } from '@/locales/locales'

const { t } = useI18n()
const localeStore = useLocaleStore()

const selectedLocale = computed({
  get: () => localeStore.currentCode,
  set: (code: LocaleCode) => localeStore.setLocale(code),
})

const getDisplayName = (code: LocaleCode) => {
  const localeData = AVAILABLE_LOCALES.find((l) => l.code === code)
  const [lang = ''] = code.split('-')
  return localeData ? `${lang.toUpperCase()} – ${localeData.name}` : code
}
</script>

<template>
  <div class="language-switcher">
    <select v-model="selectedLocale" :aria-label="t('language.selectAriaLabel')">
      <option
        v-for="localeItem in AVAILABLE_LOCALES"
        :key="localeItem.code"
        :value="localeItem.code"
      >
        {{ getDisplayName(localeItem.code) }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.language-switcher {
  display: flex;
  align-items: center;
  border: none;
  border-radius: 16px;
  padding: 4px 16px;
  background-color: var(--color-text-primary);
  color: var(--color-black);
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0px 4px 12px rgba(var(--color-bkg), 0.1);
  transition: var(--transition);
}

.language-switcher select {
  color: var(--color-bkg);
  background: var(--color-text-primary);
  border: none;
  outline: none;
  cursor: pointer;
  font-family: inherit;
  font-size: inherit;
  font-weight: inherit;
  transition: var(--transition);
}

.language-switcher option {
  color: var(--color-bkg);
  background: var(--color-text-primary);
  transition: var(--transition);
}
</style>
