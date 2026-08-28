<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chatStore/chatStore'
import MessageItem from '@/components/features/chat/MessageItem.vue'
import ChatInput from '@/components/features/chat/ChatInput.vue'

const route = useRoute()
const chatStore = useChatStore()

const inputMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const chatId = computed(() => route.params.id as string)
const messages = computed(() => chatStore.activeChatMessages)
const isStreaming = computed(() => chatStore.isStreaming)

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: isStreaming.value ? 'auto' : 'smooth',
    })
  }
}

const handleSend = async () => {
  const text = inputMessage.value.trim()
  if (!text || isStreaming.value) return

  inputMessage.value = ''
  scrollToBottom()
  await chatStore.sendMessage(chatId.value, text)
}

// Proxy events to the store
const handleLike = (id: string) => chatStore.likeMessage(chatId.value, id)
const handleDislike = (id: string) => chatStore.dislikeMessage(chatId.value, id)
const handleRegenerate = async (id: string) => await chatStore.regenerateResponse(chatId.value, id)
const handleStop = () => chatStore.stopStreaming()

// Sync the route with the store
watch(
  chatId,
  (newId) => {
    if (newId) chatStore.activeChatId = newId
  },
  { immediate: true },
)

// Auto-scroll when new messages arrive or the last message grows (streamed
// tokens/steps) — tracked as a scalar so we don't deep-diff the whole
// message history on every chunk of the LLM response.
watch(
  () => {
    const msgs = chatStore.activeChatMessages
    const last = msgs[msgs.length - 1]
    return `${msgs.length}:${last?.content.length ?? 0}:${last?.steps.length ?? 0}`
  },
  () => scrollToBottom(),
)

onMounted(() => {
  const chatId = route.params.id as string
  if (chatId) chatStore.loadChatHistory(chatId)
})

watch(
  () => route.params.id,
  (newId) => {
    if (newId) chatStore.loadChatHistory(newId as string)
  },
)
</script>

<template>
  <div class="chat-layout">
    <div ref="messagesContainer" class="messages-viewport">
      <div class="chat-wrapper">
        <MessageItem
          v-for="(msg, index) in messages"
          :key="msg.id"
          :message="msg"
          :is-streaming="isStreaming"
          :is-last="index === messages.length - 1"
          @like="handleLike"
          @dislike="handleDislike"
          @regenerate="handleRegenerate"
        />
      </div>
    </div>

    <div class="input-zone">
      <div class="input-container">
        <ChatInput
          v-model="inputMessage"
          :is-streaming="isStreaming"
          @send="handleSend"
          @stop="handleStop"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-layout {
  height: 100vh; /* Or 100% depending on the parent */
  display: flex;
  flex-direction: column;
  background: var(--color-bkg);
  position: relative;
}

.messages-viewport {
  flex: 1;
  overflow-y: auto;
  padding: 40px 20px 120px; /* Bottom padding for the input */
}

.chat-wrapper {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.input-zone {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  background: linear-gradient(to bottom, transparent, var(--color-bkg) 40%);
  pointer-events: none;
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
  pointer-events: auto;
}
</style>
