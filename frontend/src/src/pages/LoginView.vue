<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useLocaleStore } from '@/stores/locale/locale'
import { useAuthStore } from '@/stores/authStore/authStore'
import type { LocaleCode } from '@/locales/locales'
import AuthVerificationPanel from '@/components/shared/AuthVerificationPanel.vue'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const localeStore = useLocaleStore()
const authStore = useAuthStore()
const { t } = useI18n()

// 'form' is the only step reachable today — login() can only ever resolve
// 'authenticated' until the backend emits verification_required (e.g. 2FA).
const step = ref<'form' | 'verification'>('form')

// Accepts either an email or a login/username — whichever the user types.
// Detected client-side purely to route the value into the right AuthRequest
// field; the backend re-derives this itself from the value it receives.
const identifier = ref('')
const password = ref('')
const showPassword = ref(false)

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const isEmailIdentifier = computed(() => EMAIL_PATTERN.test(identifier.value.trim()))

watch([identifier, password], () => {
  if (authStore.errorCode || authStore.errorDetails) {
    authStore.clearErrors()
  }
})

const selectedLocale = computed({
  get: () => localeStore.currentCode,
  set: (val) => localeStore.setLocale(val as LocaleCode),
})

const handleSubmit = async () => {
  const value = identifier.value.trim()
  const outcome = await authStore.login({
    ...(isEmailIdentifier.value ? { email: value } : { login: value }),
    password: password.value,
  })

  if (outcome === 'authenticated') {
    router.push({ name: 'Home' })
  } else if (outcome === 'verification_required') {
    step.value = 'verification'
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-box">
      <Transition name="step-fade" mode="out-in">
        <AuthVerificationPanel
          v-if="step === 'verification' && authStore.pendingVerification"
          key="verification"
          :title="t('login.verification.title')"
          :subtitle="
            t('login.verification.subtitle', { target: authStore.pendingVerification.target })
          "
          :back-label="t('login.verification.backToLogin')"
          back-to="Login"
        />
        <div v-else key="form">
          <div class="header">
            <h1 class="title">{{ $t('login.title') }}</h1>
            <p class="subtitle">{{ $t('login.subtitle') }}</p>
          </div>

          <div v-if="authStore.errorCode" class="error-message">
            {{ $t(`errors.${authStore.errorCode}`, authStore.errorDetails || {}) }}
          </div>

          <form @submit.prevent="handleSubmit" class="form">
            <div class="input-group">
              <input
                v-model="identifier"
                type="text"
                autocomplete="username"
                :placeholder="$t('login.identifier_placeholder')"
                class="input"
                required
              />
            </div>

            <div class="input-group">
              <div class="password-field">
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  :placeholder="$t('login.password_placeholder')"
                  class="input"
                  required
                />
                <button
                  type="button"
                  class="toggle-password-btn"
                  @click="showPassword = !showPassword"
                  :aria-label="showPassword ? $t('login.hidePassword') : $t('login.showPassword')"
                  :tabindex="-1"
                >
                  <svg
                    v-if="showPassword"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path
                      d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
                    ></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
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
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
              </div>
              <div class="forgot-password">
                <a href="#" class="forgot-link">{{ $t('login.forgot_password') }}</a>
              </div>
            </div>

            <div class="actions">
              <button type="submit" class="submit-btn">{{ $t('login.submit') }}</button>
              <div class="create-account">
                <RouterLink to="/register" class="create-link">
                  {{ $t('login.create_account') }}
                </RouterLink>
              </div>
            </div>
          </form>

          <div class="footer">
            <select v-model="selectedLocale" class="lang-select">
              <option v-for="l in localeStore.AVAILABLE_LOCALES" :key="l.code" :value="l.code">
                {{ l.name }}
              </option>
            </select>
            <div class="footer-links">
              <a href="#" class="footer-link">{{ $t('login.privacy') }}</a>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
  background-color: var(--color-bkg);
}

.login-box {
  width: 100%;
  max-width: 400px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 32px;
  background-color: var(--color-bkg);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.step-fade-enter-active,
.step-fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.step-fade-enter-from {
  opacity: 0;
  transform: translateX(16px);
}
.step-fade-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

.header {
  text-align: center;
  margin-bottom: 32px;
}

.title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.subtitle {
  font-size: 14px;
  color: var(--color-text-sub);
  margin-top: 8px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-group {
  display: flex;
  flex-direction: column;
}

.input {
  width: 100%;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background-color: transparent;
  outline: none;
  color: var(--color-text-primary);
  transition:
    border 0.3s,
    box-shadow 0.3s;
}

.input:focus {
  border-color: var(--color-text-title);
  box-shadow: 0 0 0 1px var(--color-text-title);
}

.password-field {
  position: relative;
}

.password-field .input {
  padding-right: 44px;
}

.toggle-password-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-sub);
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.toggle-password-btn:hover {
  color: var(--color-text-primary);
}
.toggle-password-btn:focus {
  outline: none;
}

.forgot-password {
  text-align: right;
  margin-top: 6px;
}

.forgot-link {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-title);
  text-decoration: none;
  transition: color 0.3s;
}

.forgot-link:hover {
  color: var(--color-text-primary);
}

.actions {
  padding-top: 16px;
}

.submit-btn {
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

.submit-btn:hover {
  opacity: 0.9;
}

.submit-btn:active {
  transform: scale(0.98);
}

.create-account {
  text-align: center;
  margin-top: 12px;
}

.create-link {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-title);
  background-color: transparent;
  padding: 8px 16px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.create-link:hover {
  background-color: var(--color-bkg-soft);
}

.footer {
  margin-top: 48px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-sub);
}

.language {
  cursor: pointer;
}

.footer-links {
  display: flex;
  gap: 16px;
}

.footer-link {
  color: var(--color-text-sub);
  text-decoration: none;
  transition: color 0.3s;
}

.footer-link:hover {
  color: var(--color-text-primary);
}

.error-message {
  color: #b91c1c;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 8px;
  text-align: center;
}

.input-error {
  border-color: #ef4444;
}

.submit-btn:disabled,
.lang-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
