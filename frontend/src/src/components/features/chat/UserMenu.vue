<script setup lang="ts">
import { ref, computed, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/authStore/authStore'
import { useChatStore } from '@/stores/chatStore/chatStore'

// Whether the parent sidebar rail is expanded (controls whether the
// nickname/status text next to the avatar is shown).
const props = defineProps<{ sidebarOpen: boolean }>()

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const chatStore = useChatStore()

const menuOpen = ref(false)
const triggerRef = ref<HTMLElement | null>(null)
const menuRef = ref<HTMLElement | null>(null)
const menuStyle = ref<Record<string, string>>({})

// Nothing to open until the anonymous/real session has actually resolved.
const canOpen = computed(() => authStore.isAuthenticated && !authStore.isLoading)

// The account name shown everywhere: what the user actually typed at
// registration, falling back to email, then to a generic label — never a
// hardcoded literal.
const accountLabel = computed(
  () => authStore.user?.name || authStore.user?.email || t('userMenu.accountFallback'),
)

const userNickname = computed(() => {
  if (authStore.isLoading) return t('userMenu.connecting')
  if (authStore.isGuest) return authStore.user?.name || t('userMenu.guestTitle')
  return accountLabel.value
})

const userInitial = computed(() => {
  const name = userNickname.value.trim()
  return name ? name.charAt(0).toUpperCase() : '?'
})

const statusText = computed(() => {
  if (authStore.errorCode) return t('userMenu.statusError')
  if (authStore.isLoading) return t('userMenu.statusLoading')
  return authStore.isGuest ? t('userMenu.statusGuest') : t('userMenu.statusOnline')
})

const statusModifier = computed(() => {
  if (authStore.errorCode) return 'error'
  if (authStore.isLoading) return 'loading'
  return authStore.isGuest ? 'guest' : 'online'
})

const positionMenu = () => {
  const btn = triggerRef.value
  if (!btn) return
  const rect = btn.getBoundingClientRect()
  menuStyle.value = {
    left: `${rect.left}px`,
    bottom: `${window.innerHeight - rect.top + 8}px`,
    width: `${Math.max(rect.width, 260)}px`,
  }
}

const onClickOutside = (event: MouseEvent) => {
  const target = event.target as Node
  if (menuRef.value?.contains(target) || triggerRef.value?.contains(target)) return
  close()
}

const onKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') close()
}

const open = async () => {
  positionMenu()
  menuOpen.value = true
  await nextTick()
  document.addEventListener('click', onClickOutside)
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', positionMenu)
}

const close = () => {
  menuOpen.value = false
  document.removeEventListener('click', onClickOutside)
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', positionMenu)
}

const toggle = () => {
  if (!canOpen.value) return
  if (menuOpen.value) {
    close()
  } else {
    open()
  }
}

onBeforeUnmount(close)

const goRegister = () => {
  close()
  router.push({ name: 'Register' })
}

const goLogin = () => {
  close()
  router.push({ name: 'Login' })
}

const handleLogout = async () => {
  close()
  chatStore.resetLocalState()
  authStore.logout()
  await authStore.anonymousLogin()
  router.push({ name: 'chat-home' })
}
</script>

<template>
  <div class="user-menu">
    <button
      ref="triggerRef"
      type="button"
      class="user-profile"
      :class="{ 'is-loading': authStore.isLoading, 'is-open': menuOpen }"
      :disabled="!canOpen"
      :title="userNickname"
      :aria-expanded="menuOpen"
      @click="toggle"
    >
      <div class="avatar">{{ userInitial }}</div>
      <div class="user-info" v-show="props.sidebarOpen">
        <span class="nickname">{{ userNickname }}</span>
        <span class="status" :class="`status-${statusModifier}`">{{ statusText }}</span>
      </div>
      <svg
        v-show="props.sidebarOpen"
        class="chevron"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="18 15 12 9 6 15"></polyline>
      </svg>
    </button>

    <Teleport to="body">
      <Transition name="menu-fade">
        <div v-if="menuOpen" ref="menuRef" class="user-menu-popover" :style="menuStyle" role="menu">
          <template v-if="authStore.isGuest">
            <div class="menu-header">
              <div class="menu-avatar">{{ userInitial }}</div>
              <div class="menu-header-text">
                <div class="menu-title">{{ t('userMenu.guestTitle') }}</div>
                <div class="menu-subtitle">{{ t('userMenu.guestSubtitle') }}</div>
              </div>
            </div>

            <div class="menu-divider"></div>

            <button
              type="button"
              class="menu-item menu-item-primary"
              role="menuitem"
              @click="goRegister"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <line x1="19" y1="8" x2="19" y2="14"></line>
                <line x1="22" y1="11" x2="16" y2="11"></line>
              </svg>
              {{ t('userMenu.createAccount') }}
            </button>

            <button type="button" class="menu-item" role="menuitem" @click="goLogin">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
                <polyline points="10 17 15 12 10 7"></polyline>
                <line x1="15" y1="12" x2="3" y2="12"></line>
              </svg>
              {{ t('userMenu.haveAccount') }}
            </button>
          </template>

          <template v-else>
            <div class="menu-header">
              <div class="menu-avatar">{{ userInitial }}</div>
              <div class="menu-header-text">
                <div class="menu-title">{{ accountLabel }}</div>
                <div class="menu-subtitle">{{ authStore.user?.email }}</div>
              </div>
            </div>

            <div class="menu-divider"></div>

            <button
              type="button"
              class="menu-item menu-item-danger"
              role="menuitem"
              @click="handleLogout"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
              {{ t('userMenu.logout') }}
            </button>
          </template>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.user-menu {
  width: 100%;
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

.user-profile:disabled {
  cursor: wait;
}

.user-profile:hover,
.user-profile.is-open {
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
  flex: 1;
}

.nickname {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status {
  font-size: 11px;
  color: var(--color-text-sub);
}

.status-error {
  color: #ff4d4f;
}

.status-guest {
  color: var(--color-text-title);
}

.chevron {
  flex-shrink: 0;
  color: var(--color-text-sub);
}

.user-profile.is-loading {
  animation: pulse 1.5s infinite;
  cursor: wait;
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

.user-menu-popover {
  position: fixed;
  z-index: 1400;
  background: var(--color-bkg);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
  padding: 8px;
  display: flex;
  flex-direction: column;
}

.menu-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 8px;
}

.menu-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-text-title, #333);
  color: var(--color-bkg-mute);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 15px;
}

.menu-header-text {
  min-width: 0;
}

.menu-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-subtitle {
  font-size: 12px;
  color: var(--color-text-sub);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-divider {
  height: 1px;
  background: var(--color-border);
  margin: 4px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 8px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: var(--color-text-primary);
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s;
}

.menu-item svg {
  flex-shrink: 0;
  color: var(--color-text-sub);
}

.menu-item:hover {
  background: var(--color-bkg-soft);
}

.menu-item-primary {
  color: var(--color-text-title);
  font-weight: 500;
}

.menu-item-primary svg {
  color: var(--color-text-title);
}

.menu-item-danger:hover {
  color: #ef4444;
}

.menu-item-danger:hover svg {
  color: #ef4444;
}

.menu-fade-enter-active,
.menu-fade-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
