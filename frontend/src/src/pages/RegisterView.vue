<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useLocaleStore } from '@/stores/locale/locale'
import { useAuthStore } from '@/stores/authStore/authStore'
import type { LocaleCode } from '@/locales/locales'
import { getPasswordValidationStatus, isPasswordCompliant } from '@/utils/passwordValidator'
import type { PasswordRuleStatus } from '@/utils/passwordValidator'

const router = useRouter()
const localeStore = useLocaleStore()
const authStore = useAuthStore()

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)

const selectedLocale = computed({
  get: () => localeStore.currentCode,
  set: (val) => localeStore.setLocale(val as LocaleCode),
})

const passwordRules = computed<PasswordRuleStatus[]>(() =>
  getPasswordValidationStatus(password.value),
)
const isPasswordTouched = computed(() => password.value.length > 0)
const isPasswordValid = computed(() => isPasswordCompliant(password.value))
const isPasswordMatch = computed(
  () => confirmPassword.value.length > 0 && confirmPassword.value === password.value,
)

watch([name, email, password, confirmPassword], () => {
  if (authStore.errorCode) {
    authStore.errorCode = null
    authStore.errorDetails = null
  }
})

const handleSubmit = async () => {
  if (isPasswordTouched.value && !isPasswordValid.value) {
    authStore.errorCode = 'VALIDATION_PASSWORD_INVALID'
    authStore.errorDetails = null
    return
  }
  if (confirmPassword.value.length > 0 && !isPasswordMatch.value) {
    authStore.errorCode = 'VALIDATION_PASSWORDS_MISMATCH'
    authStore.errorDetails = null
    return
  }

  const success = await authStore.register({
    name: name.value.trim(),
    email: email.value.trim(),
    password: password.value,
  })

  if (success) router.push({ name: 'login' })
}
</script>

<template>
  <div class="login-container">
    <div class="login-box">
      <div class="header">
        <h1 class="title">{{ $t('register.title') }}</h1>
        <p class="subtitle">{{ $t('register.subtitle') }}</p>
      </div>

      <div v-if="authStore.errorCode" class="error-message">
        {{ $t(`errors.${authStore.errorCode}`, authStore.errorDetails || {}) }}
      </div>

      <form @submit.prevent="handleSubmit" class="form">
        <div class="input-group">
          <input
            v-model="name"
            type="text"
            :placeholder="$t('register.name_placeholder')"
            class="input"
            required
            autocomplete="name"
            :disabled="authStore.isLoading"
          />
        </div>

        <div class="input-group">
          <input
            v-model="email"
            type="email"
            :placeholder="$t('register.email_placeholder')"
            class="input"
            required
            autocomplete="email"
            :disabled="authStore.isLoading"
          />
        </div>

        <div class="input-group password-group">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            :placeholder="$t('register.password_placeholder')"
            class="input"
            :class="{ 'input-error': isPasswordTouched && !isPasswordValid }"
            required
            autocomplete="new-password"
            :disabled="authStore.isLoading"
          />
          <button
            type="button"
            class="toggle-password-btn"
            @click="showPassword = !showPassword"
            :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
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

        <!-- CheckList -->
        <div
          v-if="isPasswordTouched"
          class="password-rules"
          role="list"
          aria-label="Требования к паролю"
        >
          <div
            v-for="rule in passwordRules"
            :key="rule.id"
            class="rule-item"
            :class="{ success: rule.status }"
            role="listitem"
          >
            <span class="rule-icon">{{ rule.status ? '✓' : '○' }}</span>
            <span class="rule-text">{{ $t(`validation.${rule.label}`) }}</span>
          </div>
        </div>

        <div class="input-group">
          <input
            v-model="confirmPassword"
            type="password"
            :placeholder="$t('register.confirm_password_placeholder')"
            class="input"
            :class="{
              'input-error': confirmPassword.length > 0 && !isPasswordMatch,
              'input-success': isPasswordMatch,
            }"
            required
            autocomplete="new-password"
            :disabled="authStore.isLoading"
          />
        </div>

        <div class="actions">
          <button type="submit" class="submit-btn" :disabled="authStore.isLoading">
            <span v-if="authStore.isLoading">{{
              $t('register.loading') || 'Создание аккаунта...'
            }}</span>
            <span v-else>{{ $t('register.submit') }}</span>
          </button>
          <div class="create-account">
            <RouterLink to="/login" class="create-link">
              {{ $t('register.already_have_account') }}
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
          <a href="#" class="footer-link">{{ $t('register.privacy') }}</a>
        </div>
      </div>
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
  gap: 16px;
}

.input-group {
  position: relative;
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

.password-group .input {
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

.input-success {
  border-color: #22c55e !important;
}
.input-success:focus {
  border-color: #22c55e !important;
  box-shadow: 0 0 0 1px #22c55e !important;
}

.input-error {
  border-color: #ef4444 !important;
}
.input-error:focus {
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 1px #ef4444 !important;
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
  text-decoration: none;
}
.create-link:hover {
  background-color: var(--color-bkg-soft);
}

.footer {
  margin-top: 32px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-sub);
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
  hyphens: auto;
  text-justify: inter-word;
}

.submit-btn:disabled,
.lang-select:disabled,
.input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.password-rules {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: -4px;
  animation: slideDown 0.2s ease-out;
}
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.rule-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-sub);
  transition: color 0.2s ease;
}
.rule-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1.5px solid currentColor;
  font-size: 10px;
  font-weight: 600;
  flex-shrink: 0;
  transition: all 0.2s ease;
}
.rule-item.success {
  color: #22c55e;
}
.rule-item.success .rule-icon {
  background-color: #22c55e;
  border-color: #22c55e;
  color: #fff;
}
</style>
