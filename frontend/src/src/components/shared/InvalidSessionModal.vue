<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore/authStore'
import { useChatStore } from '@/stores/chatStore/chatStore'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const chatStore = useChatStore()

const isRecovering = ref(false)

// Don't stack this modal on top of the page it sends the user to.
const isOnAuthRoute = computed(() => route.name === 'Login' || route.name === 'Register')
const isVisible = computed(() => authStore.invalidSession && !isOnAuthRoute.value)

// For a real account, downgrading to a fresh guest session would silently
// orphan it — send the user to re-authenticate instead. invalidSession
// stays sticky (same reasoning as sessionExpired) until a real re-auth
// succeeds, so it won't pop back up once they're on the login page.
const goToLogin = () => {
  router.push({ name: 'Login' })
}

// For a session that was already a guest, the only way out is to throw
// away whatever local state exists (it belongs to a credential the backend
// just told us was never legitimate) and mint a brand new guest session. A
// full reload afterwards guarantees no stale in-memory state survives.
const startOver = async () => {
  if (isRecovering.value) return
  isRecovering.value = true

  chatStore.resetLocalState()
  if (!authStore.isAuthenticated) {
    await authStore.anonymousLogin()
  }

  window.location.reload()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="isVisible" class="overlay" role="alertdialog" aria-modal="true">
      <div class="dialog">
        <h2 class="title">{{ $t('invalidSession.title') }}</h2>
        <p class="subtitle">
          {{
            authStore.isGuest ? $t('invalidSession.subtitle') : $t('invalidSession.subtitleAccount')
          }}
        </p>

        <div class="actions">
          <button v-if="!authStore.isGuest" type="button" class="primary-btn" @click="goToLogin">
            {{ $t('invalidSession.loginAction') }}
          </button>

          <button
            type="button"
            :class="authStore.isGuest ? 'primary-btn' : 'secondary-btn'"
            :disabled="isRecovering"
            @click="startOver"
          >
            {{ isRecovering ? $t('invalidSession.recovering') : $t('invalidSession.action') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 16px;
}

.dialog {
  width: 100%;
  max-width: 380px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 32px;
  background-color: var(--color-bkg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  text-align: center;
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
  transition: opacity 0.3s;
}

.primary-btn:hover {
  opacity: 0.9;
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.secondary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
