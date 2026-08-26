<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ChatStep } from '@/types/chat/component'

const props = defineProps<{
  steps: ChatStep[]
  isStreaming: boolean
  isLast: boolean
}>()

const { t, te } = useI18n()

// Auto-expand if this is the last message and generation is in progress
const isOpen = ref(props.isStreaming && props.isLast)

const toggle = () => {
  isOpen.value = !isOpen.value
}

// Watch the generation status: once finished, it can be left open or collapsed
watch(
  () => props.isStreaming,
  (streaming) => {
    if (streaming && props.isLast) isOpen.value = true
  },
)

const getNodeLabel = (node: string): string => {
  const key = `chat.nodes.${node}`
  // te(key) checks whether such a key exists in the dictionary
  // If the key is missing (e.g. the server sent a new status), the raw node value is returned
  return te(key) ? t(key) : node
}
</script>

<template>
  <div class="model-thinking">
    <button @click="toggle" class="thinking-toggle" type="button">
      <div class="toggle-content">
        <svg
          v-if="isStreaming && isLast"
          class="spinner"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
        >
          <circle
            cx="12"
            cy="12"
            r="10"
            stroke-width="2"
            stroke-dasharray="32"
            stroke-linecap="round"
          ></circle>
        </svg>
        <svg
          v-else
          class="chevron"
          :class="{ open: isOpen }"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
        <span class="title-text">
          {{ isStreaming && isLast ? t('chat.thinking.analyzing') : t('chat.thinking.title') }}
        </span>
      </div>
    </button>

    <Transition name="expand">
      <div v-if="isOpen" class="thinking-content">
        <div v-for="(step, i) in steps" :key="i" class="thought-item">
          <span class="thought-node">{{ getNodeLabel(step.node) }}:</span>
          <span class="thought-text">{{ step.message }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* Styles remain unchanged */
.model-thinking {
  margin-bottom: 12px;
  background: var(--color-bkg-soft);
  border-radius: 12px;
  overflow: hidden;
}

.thinking-toggle {
  width: 100%;
  background: transparent;
  border: none;
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: background 0.2s;
}

.thinking-toggle:hover {
  background: var(--color-bkg-mute);
}

.toggle-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-sub);
  font-size: 14px;
  font-weight: 500;
}

.spinner {
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
  color: #4285f4;
}

.chevron {
  width: 16px;
  height: 16px;
  transition: transform 0.3s ease;
}
.chevron.open {
  transform: rotate(180deg);
}

.thinking-content {
  padding: 0 16px 12px 32px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.thought-item {
  font-size: 13px;
  line-height: 1.5;
}

.thought-node {
  font-weight: 600;
  color: var(--color-text-primary);
  margin-right: 6px;
}

.thought-text {
  color: var(--color-text-sub);
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

/* Smooth expand (accordion) */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
  opacity: 1;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-bottom: 0;
}
</style>
