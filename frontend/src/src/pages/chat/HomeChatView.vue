<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useChatStore } from '@/stores/chatStore/chatStore'

// Interface for the prompts, for strict typing
type QuickPromptIcon = 'idea' | 'code' | 'terminal'
interface QuickPrompt {
  id: string | number
  icon: QuickPromptIcon
}

const router = useRouter()
const chatStore = useChatStore()
const { t } = useI18n()

const query = ref('')
const isSubmitting = ref(false)

// Icons only — translated text comes from chat.home.quickPrompts via index
const quickPrompts: QuickPrompt[] = [
  { id: 1, icon: 'idea' },
  { id: 2, icon: 'code' },
  { id: 3, icon: 'terminal' },
]

const handleSubmit = async (promptText?: string) => {
  // Determine whether to take the text from the argument or from the input
  const textToSubmit = (typeof promptText === 'string' ? promptText : query.value).trim()

  if (!textToSubmit || isSubmitting.value) return

  try {
    isSubmitting.value = true

    if (typeof promptText === 'string') {
      query.value = promptText
    }

    const newChatId = await chatStore.startChatWithMessage(textToSubmit)

    if (!newChatId) {
      throw new Error('Backend did not return a new chat ID')
    }

    await router.push({ name: 'chat-active', params: { id: newChatId } })
  } catch (error) {
    console.error('[HomeChatView] Failed to navigate to chat:', error)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="home-chat">
    <div class="centered-wrapper">
      <h1 class="brand-title">{{ t('chat.home.heading') }}</h1>

      <form
        @submit.prevent="handleSubmit()"
        class="input-wrapper"
        :class="{ 'is-disabled': isSubmitting }"
      >
        <input
          v-model="query"
          type="text"
          :placeholder="t('chat.home.placeholder')"
          class="main-input"
          autocomplete="off"
          autofocus
          :disabled="isSubmitting"
          :aria-label="t('chat.home.inputAriaLabel')"
          @keydown.ctrl.enter.prevent="handleSubmit()"
          @keydown.meta.enter.prevent="handleSubmit()"
        />

        <button
          type="submit"
          class="send-btn"
          :disabled="!query.trim() || isSubmitting"
          :aria-label="t('chat.home.sendAriaLabel')"
        >
          <svg
            aria-hidden="true"
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
      </form>

      <div class="quick-prompts" :aria-label="t('chat.home.quickPromptsAriaLabel')">
        <!-- Replaced <span> with <button> for proper semantics and A11y -->
        <button
          v-for="(prompt, index) in quickPrompts"
          :key="prompt.id"
          type="button"
          class="prompt-tag"
          :disabled="isSubmitting"
          @click="handleSubmit(t(`chat.home.quickPrompts.${index}`))"
        >
          <span class="prompt-icon">
            <svg
              v-if="prompt.icon === 'idea'"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1.3.5 2.6 1.5 3.5.8.8 1.3 1.5 1.5 2.5"
              ></path>
              <path d="M9 18h6"></path>
              <path d="M10 22h4"></path>
            </svg>
            <svg
              v-else-if="prompt.icon === 'code'"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="16 18 22 12 16 6"></polyline>
              <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
            <svg
              v-else
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="4 17 10 11 4 5"></polyline>
              <line x1="12" y1="19" x2="20" y2="19"></line>
            </svg>
          </span>
          {{ t(`chat.home.quickPrompts.${index}`) }}
        </button>
      </div>
    </div>
  </main>
</template>

<style scoped>
/* Use <main> for semantics instead of <div> */
.home-chat {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--color-bkg);
}

.centered-wrapper {
  width: 100%;
  max-width: 720px;
  text-align: center;
  transform: translateY(-5vh);
  animation: fadeIn 0.5s ease-out; /* Smooth screen fade-in */
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-3vh);
  }
  to {
    opacity: 1;
    transform: translateY(-5vh);
  }
}

.brand-title {
  font-size: 40px;
  font-weight: 500;
  /* Recommend extracting #8a2be2 into a variable, e.g. var(--color-brand) */
  background: linear-gradient(90deg, var(--color-text-title), #8a2be2);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 32px;
  letter-spacing: -0.5px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--color-bkg-soft, #fff);
  border: 1px solid var(--color-border);
  border-radius: 32px;
  padding: 8px 12px 8px 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transition:
    box-shadow 0.2s,
    border-color 0.2s,
    opacity 0.2s;
}

.input-wrapper:focus-within {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: var(--color-text-title);
}

.input-wrapper.is-disabled {
  opacity: 0.7;
  pointer-events: none;
}

.main-input {
  flex: 1;
  background: transparent;
  border: none;
  font-size: 16px;
  color: var(--color-text-primary);
  outline: none;
  padding: 12px 0;
  width: 100%; /* Fix for Safari */
}

.main-input::placeholder {
  color: var(--color-text-sub);
}

.send-btn {
  background: var(--color-text-title);
  color: var(--color-bkg-mute);
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition:
    opacity 0.2s,
    transform 0.1s;
  flex-shrink: 0; /* So the button doesn't get squished */
}

.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* :hover:not(:disabled) keeps the animation safe */
.send-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: scale(1.05);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.quick-prompts {
  margin-top: 32px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.prompt-icon {
  display: flex;
}

.prompt-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  font-size: 14px;
  color: var(--color-text-sub);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.prompt-tag:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.prompt-tag:hover:not(:disabled) {
  background: var(--color-bkg-soft);
  color: var(--color-text-primary);
  border-color: var(--color-text-sub);
  transform: translateY(-1px);
}
</style>
