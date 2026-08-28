<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DefaultLayout from '@/layout/DefaultLayout.vue'
import SessionExpiredModal from '@/components/shared/SessionExpiredModal.vue'
import InvalidSessionModal from '@/components/shared/InvalidSessionModal.vue'

const route = useRoute()

const layout = computed(() => route.meta.layout || DefaultLayout)
</script>

<template>
  <component :is="layout">
    <router-view />
  </component>
  <SessionExpiredModal />
  <InvalidSessionModal />
</template>
