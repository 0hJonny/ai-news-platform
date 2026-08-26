<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'

const props = defineProps<{
  modelValue: string
  isStreaming: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'send'): void
  (e: 'stop'): void
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)

const adjustHeight = async () => {
  await nextTick()
  const el = textareaRef.value
  if (!el) return

  el.style.height = '1px'
  el.style.height = `${Math.min(el.scrollHeight, 200)}px`
}

const onInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
  adjustHeight()
}

const handleKeydown = (e: KeyboardEvent) => {
  // Send on Enter (without Shift, which inserts a line break)
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault() // Prevent the default line break
    if (props.modelValue.trim() && !props.isStreaming) {
      emit('send')
    }
  }
}

watch(
  () => props.modelValue,
  (newVal) => {
    if (!newVal) {
      adjustHeight()
    }
  },
)

onMounted(() => {
  textareaRef.value?.focus()
  adjustHeight()
})
</script>

<template>
  <div class="input-card">
    <textarea
      ref="textareaRef"
      :value="modelValue"
      placeholder="Введите вопрос..."
      rows="1"
      @input="onInput"
      @keydown="handleKeydown"
    ></textarea>

    <button v-if="isStreaming" @click="emit('stop')" class="action-btn stop-btn">
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect x="6" y="6" width="12" height="12" rx="2" ry="2"></rect>
      </svg>
    </button>

    <button v-else @click="emit('send')" :disabled="!modelValue.trim()" class="action-btn send-btn">
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
      </svg>
    </button>
  </div>
</template>

<style scoped>
.input-card {
  background: var(--color-bkg-soft);
  border-radius: 24px;
  padding: 10px 16px;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.input-card:focus-within {
  border-color: var(--color-text-title);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 16px;
  line-height: 1.5;
  resize: none;
  color: var(--color-text-primary);
  max-height: 200px;

  padding: 6px 0;
  margin: 0;
  font-family: inherit;

  box-sizing: border-box;
  overflow-x: hidden;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

textarea::placeholder {
  color: var(--color-text-sub);
}

textarea::-webkit-scrollbar {
  width: 4px;
}
textarea::-webkit-scrollbar-thumb {
  background-color: var(--color-border);
  border-radius: 4px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: transparent;
  color: var(--color-text-sub);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  margin-bottom: 2px;
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.action-btn:not(:disabled):hover {
  background: var(--color-border);
  color: var(--color-text-primary);
}

.send-btn:not(:disabled) {
  background: var(--color-text-title);
  color: var(--color-bkg-mute);
}

.send-btn:not(:disabled):hover {
  transform: scale(1.05);
}

.send-btn:not(:disabled):active {
  transform: scale(0.95);
}

.stop-btn {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.stop-btn:hover {
  background: rgba(239, 68, 68, 0.2);
}
</style>
