import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createChatsRepository } from '@/services/chat'
import type { ChatEvent, FinalAnswer, RepositoryError } from '@/types/chat/chat'

// --- Local state interfaces ---

export interface Message {
  id: string // Local UUID (for :key in v-for)
  backendMessageId?: string | null // Real ID from the backend DB (appears at the end of the stream)
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt: string
  reaction?: 'like' | 'dislike' | null
  traceId?: string | null
  steps: ChatEvent[]
}

export interface Chat {
  id: string
  title: string
  lastMessage: string
  updatedAt: string
}

export const useChatStore = defineStore('chat', () => {
  // 1. Initialize the repository (automatically wires up Axios and the token)
  const repo = createChatsRepository()

  // 2. State
  const chats = ref<Chat[]>([])
  const activeChatId = ref<string | null>(null)
  const messagesMap = ref<Record<string, Message[]>>({})

  const isStreaming = ref(false)
  const isSidebarOpen = ref(false)
  const streamProgress = ref<string>('')

  const currentAbortController = ref<AbortController | null>(null)

  // 3. Getters
  const activeChatMessages = computed(() => {
    return activeChatId.value ? messagesMap.value[activeChatId.value] || [] : []
  })

  const sortedChats = computed(() => {
    return [...chats.value].sort((a, b) => {
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    })
  })

  // 4. Methods (Actions) - UI
  const toggleSidebar = () => {
    isSidebarOpen.value = !isSidebarOpen.value
  }

  const stopStreaming = () => {
    if (currentAbortController.value) {
      currentAbortController.value.abort()
      currentAbortController.value = null
    }
    isStreaming.value = false
    streamProgress.value = ''
  }

  // --- Session CRUD ---

  const loadSessions = async () => {
    const result = await repo.getSessions()
    if (result.success) {
      chats.value = result.data.map((s) => ({
        id: s.id,
        title: s.title,
        lastMessage: '', // Can be updated later once the backend starts sending a preview
        updatedAt: s.updated_at,
      }))
    } else {
      console.error('[ChatStore] Ошибка загрузки сессий:', result.error.message)
    }
  }

  const createNewChat = async (initialTitle = 'Новый чат'): Promise<Chat | null> => {
    const result = await repo.createSession({ title: initialTitle })

    if (!result.success) {
      console.error('[ChatStore] Ошибка создания сессии:', result.error.message)
      return null
    }

    const backendSession = result.data

    const newChat: Chat = {
      id: backendSession.id,
      title: backendSession.title,
      lastMessage: '',
      updatedAt: backendSession.updated_at || new Date().toISOString(),
    }

    chats.value.unshift(newChat) // Add to the front of the list
    messagesMap.value[newChat.id] = []
    activeChatId.value = newChat.id

    return newChat
  }

  const startChatWithMessage = async (text: string) => {
    const title = text.slice(0, 40) + (text.length > 40 ? '...' : '')

    const chat = await createNewChat(title)
    if (!chat) return null

    sendMessage(chat.id, text).catch((err) => {
      console.error('[ChatStore] Ошибка фоновой отправки сообщения:', err)
    })

    // 3. Return the ID immediately so the router can instantly navigate the user to the chat page
    return chat.id
  }

  // --- Message handling and Streaming ---

  const _getReactiveMessage = (chatId: string, messageId: string) => {
    return messagesMap.value[chatId]?.find((m) => m.id === messageId)
  }

  const sendMessage = async (chatId: string, text: string) => {
    if (!text.trim() || isStreaming.value) return
    activeChatId.value = chatId

    if (!messagesMap.value[chatId]) messagesMap.value[chatId] = []

    // Add the user's message locally
    messagesMap.value[chatId].push({
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      createdAt: new Date().toISOString(),
      steps: [],
    })

    // Update chat metadata
    const chat = chats.value.find((c) => c.id === chatId)
    if (chat) {
      chat.lastMessage = text
      chat.updatedAt = new Date().toISOString()

      // Background rename if this was the default title
      if (chat.title === 'Новый чат') {
        const newTitle = text.slice(0, 40)
        chat.title = newTitle
        repo.updateSessionTitle(chat.id, newTitle).catch(console.error)
      }
    }

    await generateAIResponse(chatId, text)
  }

  const generateAIResponse = async (chatId: string, promptText: string) => {
    isStreaming.value = true
    streamProgress.value = 'Инициализация...'

    const localAiMessageId = crypto.randomUUID()

    messagesMap.value[chatId]?.push({
      id: localAiMessageId,
      backendMessageId: null, // Empty initially
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
      reaction: null,
      traceId: null,
      steps: [],
    })

    currentAbortController.value = new AbortController()

    try {
      const result = await repo.streamChat(
        { session_id: chatId, question: promptText },
        (event) => {
          const currentMsg = _getReactiveMessage(chatId, localAiMessageId)
          if (!currentMsg) return

          if ('node' in event && 'message' in event) {
            currentMsg.steps.push(event as ChatEvent)
          } else if ('answer' in event && 'session_id' in event) {
            const final = event as FinalAnswer
            currentMsg.content = final.answer
            currentMsg.traceId = final.trace_id || null

            // Remember the message ID from the backend DB for later feedback
            if (final.message_id) {
              currentMsg.backendMessageId = final.message_id
            }

            streamProgress.value = 'Готово!'
          }
        },
        currentAbortController.value.signal,
      )

      if (!result.success) {
        _handleRepositoryError(result.error, chatId, localAiMessageId)
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== 'AbortError') {
        _handleRepositoryError(
          { code: 'UNKNOWN_ERROR', message: e.message || 'Unexpected error' },
          chatId,
          localAiMessageId,
        )
      }
    } finally {
      isStreaming.value = false
      streamProgress.value = ''
      currentAbortController.value = null
    }
  }

  const regenerateResponse = async (chatId: string, assistantMsgLocalId: string) => {
    const messages = messagesMap.value[chatId]
    if (!messages) return

    const index = messages.findIndex((m) => m.id === assistantMsgLocalId)
    if (index === -1) return

    const userMsg = messages
      .slice(0, index)
      .reverse()
      .find((m) => m.role === 'user')

    if (!userMsg) return

    // Remove the current response and request a new one
    messages.splice(index)
    await generateAIResponse(chatId, userMsg.content)
  }

  // --- Feedback ---

  const sendFeedback = async (
    chatId: string,
    localMessageId: string,
    rating: 'like' | 'dislike',
    comment?: string | null,
  ): Promise<boolean> => {
    const msg = _getReactiveMessage(chatId, localMessageId)

    if (!msg?.backendMessageId) {
      console.warn('[ChatStore] Фидбек отклонен: ожидается message_id от бэкенда.')
      return false
    }

    const result = await repo.sendFeedback({
      message_id: msg.backendMessageId,
      trace_id: msg.traceId || null,
      rating,
      comment: comment || null,
    })

    if (result.success && msg) {
      msg.reaction = rating
      return true
    }
    return false
  }

  const likeMessage = async (chatId: string, localMessageId: string) => {
    const msg = _getReactiveMessage(chatId, localMessageId)
    if (!msg) return

    if (msg.reaction !== 'like') {
      const success = await sendFeedback(chatId, localMessageId, 'like')
      if (success) msg.reaction = 'like'
    } else {
      msg.reaction = null // Optional: unlike logic (if the backend supports it)
    }
  }

  const dislikeMessage = async (chatId: string, localMessageId: string) => {
    const msg = _getReactiveMessage(chatId, localMessageId)
    if (!msg) return

    if (msg.reaction !== 'dislike') {
      const success = await sendFeedback(chatId, localMessageId, 'dislike')
      if (success) msg.reaction = 'dislike'
    } else {
      msg.reaction = null
    }
  }

  // --- Utilities ---

  const _handleRepositoryError = (error: RepositoryError, chatId: string, messageId: string) => {
    const currentMsg = _getReactiveMessage(chatId, messageId)
    if (currentMsg) {
      const errorText = _getLocalizedError(error.code)
      currentMsg.content += `\n\n⚠️ ${errorText}`
    }
  }

  const _getLocalizedError = (code: string): string => {
    const errors: Record<string, string> = {
      NETWORK_ERROR: 'Ошибка сети. Проверьте подключение.',
      HTTP_ERROR: 'Сервер вернул ошибку. Попробуйте позже.',
      NO_FINAL_ANSWER: 'Ответ не был получен полностью.',
      ABORTED: 'Генерация остановлена пользователем.',
      UNKNOWN_ERROR: 'Произошла неизвестная ошибка.',
    }
    return errors[code] || 'Что-то пошло не так.'
  }

  const isLoadingHistory = ref(false)

  const loadChatHistory = async (chatId: string) => {
    // If messages for this chat are already loaded locally, skip the extra request
    if (messagesMap.value[chatId] && messagesMap.value[chatId].length > 0) {
      activeChatId.value = chatId
      return
    }

    isLoadingHistory.value = true
    activeChatId.value = chatId // Switch the active chat right away for the UI

    // Initialize an empty array so the UI doesn't break
    if (!messagesMap.value[chatId]) {
      messagesMap.value[chatId] = []
    }

    const result = await repo.getSessionMessages(chatId)

    if (result.success) {
      // Map the backend response into our local Message format
      messagesMap.value[chatId] = result.data.map((msg) => ({
        id: crypto.randomUUID(), // Local ID for v-for :key
        backendMessageId: msg.id, // The same ID used to send feedback
        role: msg.role,
        content: msg.content,
        createdAt: msg.created_at,
        traceId: msg.trace_id || null,
        reaction: null, // OR msg.rating, if you add a JOIN on the backend
        steps: [], // History usually doesn't store intermediate thoughts (steps), only the final text
      }))
    } else {
      console.error('[ChatStore] Ошибка загрузки истории:', result.error.message)
    }

    isLoadingHistory.value = false
  }

  const renameChat = async (chatId: string, newTitle: string) => {
    const chat = chats.value.find((c) => c.id === chatId)
    if (!chat || !newTitle.trim() || chat.title === newTitle) return

    const oldTitle = chat.title
    chat.title = newTitle.trim() // Optimistic UI: change it right away

    const result = await repo.updateSessionTitle(chatId, newTitle.trim())
    if (!result.success) {
      chat.title = oldTitle // Roll back if the backend request failed
      console.error('[ChatStore] Ошибка переименования:', result.error.message)
    }
  }

  const deleteChat = async (chatId: string): Promise<boolean> => {
    const result = await repo.deleteSession(chatId)

    if (result.success) {
      chats.value = chats.value.filter((c) => c.id !== chatId)
      delete messagesMap.value[chatId]

      // If the active chat was deleted, clear the selection
      if (activeChatId.value === chatId) {
        activeChatId.value = null
      }
      return true
    }

    console.error('[ChatStore] Ошибка удаления:', result.error.message)
    return false
  }

  return {
    chats,
    activeChatId,
    activeChatMessages,
    isStreaming,
    isSidebarOpen,
    streamProgress,
    sortedChats,
    isLoadingHistory,
    loadChatHistory,
    loadSessions,
    createNewChat,
    startChatWithMessage,
    toggleSidebar,
    sendMessage,
    stopStreaming,
    likeMessage,
    dislikeMessage,
    sendFeedback,
    regenerateResponse,
    renameChat,
    deleteChat,
  }
})
