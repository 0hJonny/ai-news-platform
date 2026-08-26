<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DefaultLayout from '@/layout/DefaultLayout.vue'

const route = useRoute()

const layout = computed(() => route.meta.layout || DefaultLayout)
</script>

<template>
  <component :is="layout">
    <router-view />
  </component>
</template>
