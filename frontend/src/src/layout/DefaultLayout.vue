<script setup lang="ts">
import AppHeader from '@/components/shared/AppHeader.vue'
import AppFooter from '@/components/shared/AppFooter.vue'
import TitleHeader from '@/components/shared/AppTitle.vue'

interface Props {
  titleHeader?: string
}

const props = withDefaults(defineProps<Props>(), {
  titleHeader: 'IT NEWS',
})
</script>

<template>
  <div class="layout">
    <AppHeader />
    <TitleHeader :title-header="props.titleHeader" />
    <main class="layout__main">
      <slot />
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  min-height: 100lvh;
}

.layout__main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}
</style>
