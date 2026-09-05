<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ChatMessage } from '@/types/chat/component'
import ThinkingBlock from './ThinkingBlock.vue'
import { renderMarkdown } from '@/utils/markdown'

const { t } = useI18n()

const props = defineProps<{
  message: ChatMessage
  isStreaming: boolean
  isLast: boolean
}>()

const emit = defineEmits<{
  (e: 'like', id: string): void
  (e: 'dislike', id: string): void
  (e: 'regenerate', id: string): void
}>()

const isCopied = ref(false)

const copyText = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy text:', err)
  }
}

const renderedContent = computed(() => {
  return props.message.role === 'assistant'
    ? renderMarkdown(props.message.content)
    : props.message.content
})
</script>

<template>
  <div :class="['message-row', message.role]">
    <div v-if="message.role === 'assistant'" class="ai-avatar">
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path
          d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"
        />
      </svg>
    </div>

    <div v-if="message.role === 'user'" class="actions user-actions">
      <button @click="copyText" class="icon-btn" :title="t('chat.message.copy')">
        <svg
          v-if="isCopied"
          class="icon-success"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <svg
          v-else
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      </button>
    </div>

    <div class="message-content">
      <ThinkingBlock
        v-if="message.role === 'assistant' && message.steps?.length"
        :steps="message.steps"
        :is-streaming="isStreaming"
        :is-last="isLast"
      />

      <div
        class="text-body"
        :class="{ 'markdown-body': message.role === 'assistant' }"
        v-html="renderedContent"
      ></div>

      <span
        v-if="isStreaming && isLast && message.role === 'assistant'"
        class="streaming-cursor"
      ></span>

      <div
        v-if="message.role === 'assistant' && (!isStreaming || !isLast)"
        class="actions ai-actions"
      >
        <button @click="copyText" class="icon-btn" :title="t('chat.message.copy')">
          <svg
            v-if="isCopied"
            class="icon-success"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
        </button>

        <div class="divider"></div>

        <button
          @click="emit('like', message.id)"
          class="icon-btn"
          :class="{ 'active-like': message.reaction === 'like' }"
          :disabled="isStreaming"
          :title="t('chat.message.like')"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"
            ></path>
          </svg>
        </button>

        <button
          @click="emit('dislike', message.id)"
          class="icon-btn"
          :class="{ 'active-dislike': message.reaction === 'dislike' }"
          :disabled="isStreaming"
          :title="t('chat.message.dislike')"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"
            ></path>
          </svg>
        </button>

        <button
          @click="emit('regenerate', message.id)"
          class="icon-btn"
          :disabled="isStreaming"
          :title="t('chat.message.regenerate')"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M21 2v6h-6"></path>
            <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
            <path d="M3 22v-6h6"></path>
            <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-row {
  display: flex;
  gap: 16px;
  position: relative;
  /* Add bottom spacing so the actions don't stick to the next message */
  margin-bottom: 8px;
}

.message-row.user {
  justify-content: flex-end;
}

.ai-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #4285f4, #9b72cb);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(155, 114, 203, 0.2);
}

.message-content {
  max-width: 80%;
}

.user .message-content {
  background: var(--color-bkg-soft);
  padding: 12px 20px;
  border-radius: 20px 20px 4px 20px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-text-primary);
}

.assistant .message-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 16px;
  line-height: 1.6;
  color: var(--color-text-primary);
  min-width: 0;
}

.text-body {
  width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
  color: inherit;
}

.streaming-cursor {
  display: inline-block;
  width: 5px;
  height: 1.1em;
  background: #4285f4;
  margin-left: 4px;
  border-radius: 2px;
  vertical-align: text-bottom;
  animation: blink 1s step-start infinite;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

/* --- Action buttons visibility logic --- */
.actions {
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

/* Always visible on mobile */
@media (max-width: 768px) {
  .actions {
    opacity: 1;
  }
}

.message-row:hover .actions,
.actions:focus-within {
  opacity: 1;
}

.user-actions {
  align-self: center;
  margin-right: 8px;
}
.ai-actions {
  margin-top: 8px;
  margin-bottom: -16px; /* Compensate for the visual spacing */
}

/* --- Icon button styles --- */
.icon-btn {
  width: 32px; /* Slightly enlarged for easier clicking */
  height: 32px;
  border: none;
  background: transparent;
  color: var(--color-text-sub);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Set the SVG size inside the button */
.icon-btn svg {
  width: 16px;
  height: 16px;
}

.icon-success {
  color: #10b981;
}

.icon-btn:not(:disabled):hover {
  background: var(--color-bkg-soft, rgba(0, 0, 0, 0.05));
  color: var(--color-text-primary);
}

.icon-btn:not(:disabled):active {
  transform: scale(0.92);
}

.icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Active states for feedback ratings */
.icon-btn.active-like {
  color: #4285f4;
  background: rgba(66, 133, 244, 0.1);
}
.icon-btn.active-like svg {
  fill: rgba(66, 133, 244, 0.2); /* Slight fill inside */
}

.icon-btn.active-dislike {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}
.icon-btn.active-dislike svg {
  fill: rgba(239, 68, 68, 0.2);
}

.divider {
  width: 1px;
  height: 16px;
  background-color: var(--color-border);
  margin: 0 6px;
}

:deep(.markdown-body) {
  font-family: inherit;
  font-size: 16px;
  line-height: 1.65;
  color: var(--color-text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* Paragraphs */
:deep(.markdown-body p) {
  margin-top: 0;
  margin-bottom: 1.25em;
}
:deep(.markdown-body p:last-child) {
  margin-bottom: 0;
}

/* Text emphasis */
:deep(.markdown-body strong),
:deep(.markdown-body b) {
  font-weight: 600;
  color: var(--color-text-title, var(--color-text-primary));
}

:deep(.markdown-body em),
:deep(.markdown-body i) {
  font-style: italic;
  color: var(--color-text-sub);
}

/* --- LISTS --- */
:deep(.markdown-body ul),
:deep(.markdown-body ol) {
  margin-top: 0;
  margin-bottom: 1.25em;
  padding-left: 1.5em;
}

:deep(.markdown-body li) {
  margin-bottom: 0.5em;
  line-height: 1.6;
}
:deep(.markdown-body li:last-child) {
  margin-bottom: 0;
}

/* Style the list markers for a nicer look */
:deep(.markdown-body li::marker) {
  color: var(--color-text-sub); /* Makes list bullets slightly dimmer than the text */
}

/* --- LINKS --- */
:deep(.markdown-body a) {
  color: #4285f4; /* Or var(--color-primary) */
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.2s ease;
  word-break: break-all; /* So long URLs don't break the layout */
}

:deep(.markdown-body a:hover) {
  border-bottom-color: #4285f4;
}

:deep(.markdown-body a[target='_blank']::after) {
  content: ' ↗';
  font-size: 0.8em;
  opacity: 0.7;
  display: inline-block;
  margin-left: 2px;
}

/* --- INTERACTIVE CITATIONS (Pills) --- */
/* Styles for the [1] badges we generate via regex */
:deep(.markdown-body .citation-badge) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #4285f4;
  background-color: rgba(66, 133, 244, 0.1);
  padding: 0 6px;
  margin: 0 4px;
  border-radius: 12px;
  cursor: pointer;
  user-select: none;
  vertical-align: middle;
  transform: translateY(-1px); /* Slight lift above the baseline */
  transition: all 0.2s ease;
}

:deep(.markdown-body .citation-badge:hover) {
  background-color: rgba(66, 133, 244, 0.2);
  transform: translateY(-2px);
}

/* --- HEADINGS AND DIVIDERS --- */
:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3),
:deep(.markdown-body h4) {
  margin-top: 1.5em;
  margin-bottom: 0.75em;
  font-weight: 600;
  line-height: 1.3;
  color: var(--color-text-title, var(--color-text-primary));
}

:deep(.markdown-body h1) {
  font-size: 1.5em;
}
:deep(.markdown-body h2) {
  font-size: 1.25em;
}
:deep(.markdown-body h3) {
  font-size: 1.1em;
}

:deep(.markdown-body hr) {
  height: 1px;
  background-color: var(--color-border);
  border: none;
  margin: 2em 0;
}

/* --- BLOCKQUOTES --- */
:deep(.markdown-body blockquote) {
  margin: 1.5em 0;
  padding: 0.75em 1em;
  border-left: 4px solid var(--color-border);
  background-color: var(--color-bkg-soft);
  color: var(--color-text-sub);
  border-radius: 0 8px 8px 0;
}
:deep(.markdown-body blockquote p:last-child) {
  margin-bottom: 0;
}
</style>
