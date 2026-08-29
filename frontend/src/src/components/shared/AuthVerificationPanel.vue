<script setup lang="ts">
import { RouterLink } from 'vue-router'

// Generic "extra step required" panel shared by Login/Register once the
// backend starts returning AuthOutcome's verification_required branch —
// today nothing triggers it, but both flows already know how to swap this
// in instead of redirecting.
defineProps<{
  title: string
  subtitle: string
  backLabel: string
  backTo: string
}>()
</script>

<template>
  <div class="verification-panel">
    <div class="verification-icon" aria-hidden="true">
      <svg
        width="36"
        height="36"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect width="20" height="16" x="2" y="4" rx="2"></rect>
        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
      </svg>
    </div>
    <h2 class="title">{{ title }}</h2>
    <p class="subtitle">{{ subtitle }}</p>
    <RouterLink :to="{ name: backTo }" class="back-link">{{ backLabel }}</RouterLink>
  </div>
</template>

<style scoped>
.verification-panel {
  text-align: center;
  padding: 8px 0 4px;
}

.verification-icon {
  display: flex;
  justify-content: center;
  color: var(--color-text-title);
  margin-bottom: 16px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.subtitle {
  font-size: 14px;
  color: var(--color-text-sub);
  margin-top: 8px;
  line-height: 1.5;
}

.back-link {
  display: inline-block;
  margin-top: 24px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-title);
  text-decoration: none;
}

.back-link:hover {
  text-decoration: underline;
}
</style>
