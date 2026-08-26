<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chatStore/chatStore'
import { useAuthStore } from '@/stores/authStore/authStore'
import ThemeSwitcherCompact from '@/components/shared/ThemeSwitcherCompact.vue'

const chatStore = useChatStore()
const authStore = useAuthStore()
const router = useRouter()

const isOpen = computed(() => chatStore.isSidebarOpen)

const toggleSidebar = () => {
  chatStore.isSidebarOpen = !chatStore.isSidebarOpen
}

const isMobile = ref(false)
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
}

const closeOnMobile = () => {
  if (isMobile.value && isOpen.value) {
    chatStore.isSidebarOpen = false
  }
}

const userNickname = computed(() => {
  if (authStore.isLoading) return 'Подключение...'
  // return authStore.user?.user_name || authStore.user?.email || 'Аноним'
  return 'Аноним'
})

const userInitial = computed(() => {
  if (authStore.isLoading) return '...'
  const name = userNickname.value.trim()
  return name ? name.charAt(0).toUpperCase() : '?'
})

const initAuth = async () => {
  if (!authStore.isAuthenticated) {
    const success = await authStore.anonymousLogin()
    if (!success) {
      console.error('Не удалось авторизоваться, список чатов не будет загружен.')
      return
    }
  }

  await chatStore.loadSessions()

  const urlChatId = router.currentRoute.value.params.id as string
  if (urlChatId) {
    await chatStore.loadChatHistory(urlChatId)
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  initAuth()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

const handleNewChat = () => {
  // Block chat creation if there's no token
  if (!authStore.isAuthenticated) return

  router.push({ name: 'chat-home' })
  closeOnMobile()
}

const handleSelectChat = async (id: string) => {
  await chatStore.loadChatHistory(id)

  router.push({ name: 'chat-active', params: { id } })
  closeOnMobile()
}

const editingChatId = ref<string | null>(null)
const editingTitle = ref('')

const startRename = (chatId: string, currentTitle: string, event: Event) => {
  event.stopPropagation()
  editingChatId.value = chatId
  editingTitle.value = currentTitle

  nextTick(() => {
    const input = document.getElementById(`edit-input-${chatId}`) as HTMLInputElement
    if (input) {
      input.focus()
      input.select()
    }
  })
}

const saveRename = async () => {
  if (editingChatId.value) {
    await chatStore.renameChat(editingChatId.value, editingTitle.value)
    editingChatId.value = null
  }
}

const cancelRename = () => {
  editingChatId.value = null
}

const handleDelete = async (chatId: string, event: Event) => {
  event.stopPropagation()
  if (confirm('Удалить этот чат? Действие необратимо.')) {
    const success = await chatStore.deleteChat(chatId)
    // If the deleted chat was the open one — redirect to the home screen (New chat)
    if (success && chatStore.activeChatId === null) {
      router.push({ name: 'chat-home' }) // Replace with the name of your default route
    }
  }
}
</script>

<template>
  <Transition name="fade">
    <div v-if="isOpen" class="sidebar-overlay" @click="toggleSidebar" aria-hidden="true"></div>
  </Transition>

  <button
    v-show="!isOpen"
    class="mobile-toggle-btn"
    @click="toggleSidebar"
    aria-label="Открыть меню"
  >
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <line x1="3" y1="12" x2="21" y2="12"></line>
      <line x1="3" y1="6" x2="21" y2="6"></line>
      <line x1="3" y1="18" x2="21" y2="18"></line>
    </svg>
  </button>

  <aside class="sidebar" :class="{ open: isOpen, collapsed: !isOpen }">
    <div class="sidebar-header">
      <div class="header-top-row">
        <button
          class="sidebar-toggle-btn"
          @click="toggleSidebar"
          :aria-label="isOpen ? 'Скрыть панель' : 'Показать панель'"
        >
          <svg
            v-if="isOpen"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="9" y1="3" x2="9" y2="21"></line>
          </svg>
          <svg
            v-else
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="15" y1="3" x2="15" y2="21"></line>
          </svg>
        </button>

        <ThemeSwitcherCompact v-show="isOpen" />
      </div>

      <button
        class="new-chat-btn"
        @click="handleNewChat"
        :disabled="authStore.isLoading || !authStore.isAuthenticated"
        :aria-label="isOpen ? 'Новый чат' : 'Создать чат'"
      >
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
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        <span class="btn-text" v-show="isOpen">Новый чат</span>
      </button>
    </div>

    <div class="sidebar-content">
      <div class="section-title" v-show="isOpen" v-if="chatStore.chats.length > 0">Недавние</div>

      <nav class="chat-list" role="list">
        <div v-if="chatStore.chats.length === 0" class="empty-state">
          {{ isOpen ? 'Нет активных чатов' : '' }}
        </div>

        <button
          v-for="chat in chatStore.chats"
          :key="chat.id"
          class="chat-item"
          :class="{ active: chat.id === chatStore.activeChatId }"
          @click="editingChatId !== chat.id && handleSelectChat(chat.id)"
          :title="chat.title"
          role="listitem"
        >
          <svg
            class="chat-icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>

          <!-- INLINE EDITING -->
          <input
            v-if="editingChatId === chat.id"
            :id="`edit-input-${chat.id}`"
            v-model="editingTitle"
            type="text"
            class="rename-input"
            @blur="saveRename"
            @keyup.enter="saveRename"
            @keyup.escape="cancelRename"
            @click.stop
          />

          <!-- NORMAL DISPLAY -->
          <template v-else>
            <span class="chat-title" v-show="isOpen">{{ chat.title }}</span>

            <!-- Action buttons (only when the sidebar is open) -->
            <div v-show="isOpen" class="chat-item-actions">
              <div
                class="action-btn"
                @click="startRename(chat.id, chat.title, $event)"
                title="Переименовать"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
                </svg>
              </div>
              <div
                class="action-btn delete-btn"
                @click="handleDelete(chat.id, $event)"
                title="Удалить"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path
                    d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                  ></path>
                </svg>
              </div>
            </div>
          </template>
        </button>
      </nav>
    </div>

    <div class="sidebar-footer">
      <button
        class="user-profile"
        :title="userNickname"
        :class="{ 'is-loading': authStore.isLoading }"
      >
        <div class="avatar">{{ userInitial }}</div>
        <div class="user-info" v-show="isOpen">
          <span class="nickname">{{ userNickname }}</span>
          <span class="status" :class="{ 'status-error': authStore.errorCode }">
            {{
              authStore.errorCode
                ? 'Ошибка сети'
                : authStore.isAuthenticated
                  ? 'Онлайн'
                  : 'Авторизация...'
            }}
          </span>
        </div>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 260px;
  height: 100%;
  background: var(--color-bkg-soft); /* Your original colors, restored */
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
  z-index: 100;
}

.sidebar.collapsed {
  width: 68px;
}

/* 🔝 Header */
.sidebar-header {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.sidebar-toggle-btn {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--color-text-sub);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  /* align-self: flex-start; */
  margin-left: 2px;
}

.sidebar.collapsed .header-top-row {
  justify-content: center;
}

.sidebar-toggle-btn:hover {
  background: var(--color-border);
  color: var(--color-text-primary);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  height: 40px;
  width: 100%;
  background: var(--color-bkg);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  color: var(--color-text-primary);
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.new-chat-btn:hover {
  background: var(--color-border);
  border-color: var(--color-text-sub);
}

.sidebar.collapsed .new-chat-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  padding: 0;
  justify-content: center;
  margin: 0 auto;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
  display: flex;
  flex-direction: column;
}

.sidebar-content::-webkit-scrollbar {
  width: 4px;
}
.sidebar-content::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 4px;
}

.section-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-sub);
  padding: 16px 12px 8px;
}

.empty-state {
  padding: 20px 12px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-sub);
  white-space: nowrap;
  overflow: hidden;
}

.chat-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 20px; /* "Pill" effect */
  background: transparent;
  border: 1px solid transparent;
  color: var(--color-text-primary);
  cursor: pointer;
  text-align: left;
  transition:
    background 0.2s,
    border-color 0.2s;
  white-space: nowrap;
  overflow: hidden;
  height: 44px;
  position: relative;
}

.chat-item-actions {
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  pointer-events: none;
  border-radius: 0 20px 20px 0;
  background: linear-gradient(90deg, transparent 0%, var(--color-bkg) 30%);
  padding-left: 24px;
  padding-right: 12px;
  transition: opacity 0.2s ease;
}

.chat-item.active .chat-item-actions {
  background: linear-gradient(90deg, transparent 0%, var(--color-bkg) 30%);
}

.chat-item:not(.active):hover .chat-item-actions {
  background: linear-gradient(90deg, transparent 0%, var(--color-border) 30%);
}

.chat-item:hover .chat-item-actions {
  opacity: 1;
  pointer-events: auto;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  color: var(--color-text-sub);
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

.action-btn:hover {
  background: var(--color-bkg-mute);
  color: var(--color-text-primary);
}

.delete-btn:hover {
  background: var(--color-bkg-mute);
  color: #ef4444; /* Red color on hover for delete */
}

.rename-input {
  flex: 1;
  background: var(--color-bkg);
  border: 1px solid var(--color-border); /* Focus highlight color */
  border-radius: 4px;
  color: var(--color-text-primary);
  font-size: 14px;
  padding: 4px 8px;
  margin: -5px 0; /* Compensate for the input's padding so it doesn't inflate the row height */
  outline: none;
  width: 100%;
}

.sidebar.collapsed .chat-item {
  padding: 10px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  justify-content: center;
  margin: 0 auto;
}

.chat-item:hover {
  background: var(--color-border);
}

.chat-item.active {
  background: var(--color-bkg);
  border: 1px solid var(--color-border);
  font-weight: 500;
}

.chat-icon {
  flex-shrink: 0;
  color: var(--color-text-sub);
}

.chat-title {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bkg-soft);
}

.user-profile {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 20px;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

.sidebar.collapsed .user-profile {
  padding: 8px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  justify-content: center;
  margin: 0 auto;
}

.user-profile:hover {
  background: var(--color-border);
}

.avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-text-title, #333);
  color: var(--color-bkg-mute);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  text-align: left;
}

.nickname {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
}

.status {
  font-size: 11px;
  color: var(--color-text-sub);
}

.new-chat-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.user-profile.is-loading {
  animation: pulse 1.5s infinite;
  cursor: wait;
}

.status-error {
  color: #ff4d4f !important;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
  100% {
    opacity: 1;
  }
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.4);
  z-index: 90;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    transform: translateX(0);
    box-shadow: 2px 0 12px rgba(0, 0, 0, 0.15);
  }

  .sidebar.collapsed {
    /* Fully hide the menu on mobile */
    transform: translateX(-100%);
    width: 260px; /* Keep the width for a smooth animation */
  }
}

.mobile-toggle-btn {
  display: flex;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 50;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--color-bkg-soft);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

.mobile-toggle-btn:active {
  transform: scale(0.95);
}
</style>
