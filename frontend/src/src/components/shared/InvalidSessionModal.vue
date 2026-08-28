<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/authStore/authStore'
import { useChatStore } from '@/stores/chatStore/chatStore'

const authStore = useAuthStore()
const chatStore = useChatStore()

const isRecovering = ref(false)

// The only way out of this screen: throw away whatever local state exists
// (it belongs to a credential the backend just told us was never legitimate)
// and mint a brand new guest session. A full reload afterwards guarantees no
// stale in-memory state survives the recovery.
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
    <div v-if="authStore.invalidSession" class="overlay" role="alertdialog" aria-modal="true">
      <div class="dialog">
        <h2 class="title">{{ $t('invalidSession.title') }}</h2>
        <p class="subtitle">{{ $t('invalidSession.subtitle') }}</p>

        <button type="button" class="primary-btn" :disabled="isRecovering" @click="startOver">
          {{ isRecovering ? $t('invalidSession.recovering') : $t('invalidSession.action') }}
        </button>
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

.primary-btn {
  width: 100%;
  margin-top: 24px;
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
</style>
