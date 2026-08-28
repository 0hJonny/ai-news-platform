<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore/authStore'
import { useChatStore } from '@/stores/chatStore/chatStore'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const chatStore = useChatStore()

// The Login/Register pages already give the user what this modal offers, so
// don't show it on top of them. Note this does NOT clear authStore.sessionExpired
// itself — that flag stays sticky until a real re-auth succeeds or the user
// explicitly continues as a guest, otherwise navigating here and pressing
// "back" would let SidebarChat's auto-anonymous-login silently mint a new
// guest session and orphan the current chat history.
const isOnAuthRoute = computed(() => route.name === 'Login' || route.name === 'Register')
const isVisible = computed(() => authStore.sessionExpired && !isOnAuthRoute.value)

const goTo = (name: 'Login' | 'Register') => {
  router.push({ name })
}

// Explicit user choice to abandon the expired session and start a brand new
// guest one. Resets local chat state first so the new anonymous identity
// never inherits the previous session's (now inaccessible) chat history.
const continueAsGuest = async () => {
  chatStore.resetLocalState()
  authStore.dismissSessionExpired()
  await authStore.anonymousLogin()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="isVisible" class="overlay" @click.self="authStore.dismissSessionExpired()">
        <div class="dialog" role="dialog" aria-modal="true">
          <button
            class="close-btn"
            type="button"
            :aria-label="$t('sessionExpired.dismiss')"
            @click="authStore.dismissSessionExpired()"
          >
            &times;
          </button>

          <h2 class="title">{{ $t('sessionExpired.title') }}</h2>
          <p class="subtitle">{{ $t('sessionExpired.subtitle') }}</p>

          <div class="actions">
            <button type="button" class="primary-btn" @click="goTo('Register')">
              {{ $t('sessionExpired.registerBtn') }}
            </button>
            <button type="button" class="secondary-btn" @click="goTo('Login')">
              {{ $t('sessionExpired.loginBtn') }}
            </button>
          </div>

          <button type="button" class="dismiss-link" @click="continueAsGuest">
            {{ $t('sessionExpired.dismiss') }}
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.dialog {
  position: relative;
  width: 100%;
  max-width: 380px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 32px;
  background-color: var(--color-bkg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  text-align: center;
}

.close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  background: none;
  border: none;
  font-size: 20px;
  line-height: 1;
  color: var(--color-text-sub);
  cursor: pointer;
  padding: 4px;
}

.close-btn:hover {
  color: var(--color-text-primary);
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
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 24px;
}

.primary-btn {
  width: 100%;
  padding: 12px;
  background-color: var(--color-text-title);
  color: white;
  font-weight: 500;
  border-radius: 8px;
  transition:
    opacity 0.3s,
    transform 0.2s;
}

.primary-btn:hover {
  opacity: 0.9;
}

.primary-btn:active {
  transform: scale(0.98);
}

.secondary-btn {
  width: 100%;
  padding: 12px;
  background-color: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  font-weight: 500;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.secondary-btn:hover {
  background-color: var(--color-bkg-soft);
}

.dismiss-link {
  display: block;
  margin: 16px auto 0;
  background: none;
  border: none;
  font-size: 13px;
  color: var(--color-text-sub);
  cursor: pointer;
  text-decoration: underline;
}

.dismiss-link:hover {
  color: var(--color-text-primary);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
