<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useLocaleStore } from '@/stores/locale/locale'
import { useAuthStore } from '@/stores/authStore/authStore'
import type { LocaleCode } from '@/locales/locales'
import { getPasswordValidationStatus, isPasswordCompliant } from '@/utils/passwordValidator'
import type { PasswordRuleStatus } from '@/utils/passwordValidator'
import {
  getLoginValidationStatus,
  isLoginFormatValid,
  suggestLoginFromName,
  suggestLoginAlternatives,
} from '@/utils/loginValidator'
import type { LoginRuleStatus } from '@/utils/loginValidator'
import AuthVerificationPanel from '@/components/shared/AuthVerificationPanel.vue'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const localeStore = useLocaleStore()
const authStore = useAuthStore()
const { t } = useI18n()

// The wizard steps shown as cards: 'info'/'username'/'password' are the
// data-entry steps (dots below track progress through these three),
// 'verification' is the rare backend-driven extra-confirmation branch, and
// 'success' is the terminal confirmation screen shown once registration
// actually completes — replaces the old immediate redirect.
const FORM_STEPS = ['info', 'username', 'password'] as const
type FormStep = (typeof FORM_STEPS)[number]
const step = ref<FormStep | 'verification' | 'success'>('info')

const currentStepIndex = computed(() => FORM_STEPS.indexOf(step.value as FormStep))

const name = ref('')
const email = ref('')
const login = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)

// Whether the user has typed into the login field directly — while false,
// it auto-fills from `name` (like a document title following its filename
// until you rename one by hand).
const loginTouched = ref(false)
const loginSuggestions = ref<string[]>([])
type LoginAvailability = 'idle' | 'checking' | 'available' | 'taken'
const loginAvailability = ref<LoginAvailability>('idle')

const loginRules = computed<LoginRuleStatus[]>(() => getLoginValidationStatus(login.value))
const isLoginTouched = computed(() => login.value.length > 0)
const isLoginValid = computed(() => isLoginFormatValid(login.value))

watch(name, (newName) => {
  if (loginTouched.value) return
  login.value = suggestLoginFromName(newName)
})

const onLoginInput = () => {
  loginTouched.value = true
}

const pickLoginSuggestion = (suggestion: string) => {
  loginTouched.value = true
  login.value = suggestion
}

// Debounced, cancellable availability check: every new value aborts
// whatever check is still in flight so a slow early response can't land
// after a faster later one and show stale availability.
let availabilityController: AbortController | null = null
let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(login, (value) => {
  loginSuggestions.value = []
  availabilityController?.abort()
  if (debounceTimer) clearTimeout(debounceTimer)

  if (!isLoginFormatValid(value)) {
    loginAvailability.value = 'idle'
    return
  }

  loginAvailability.value = 'checking'
  debounceTimer = setTimeout(() => void runAvailabilityCheck(value), 500)
})

const runAvailabilityCheck = async (value: string) => {
  const controller = new AbortController()
  availabilityController = controller

  const result = await authStore.checkLoginAvailability(value, controller.signal)

  // Stale: superseded by a newer keystroke while this request was in flight.
  if (controller.signal.aborted || login.value !== value) return

  if (!result.success) {
    loginAvailability.value = 'idle'
    return
  }

  if (result.data.available) {
    loginAvailability.value = 'available'
  } else {
    loginAvailability.value = 'taken'
    loginSuggestions.value = suggestLoginAlternatives(value)
  }
}

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

// Per-step gating for the "Next"/"Submit" button — kept separate from the
// validators above since a step can only advance once its own fields (not
// the whole form) are satisfied.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const isInfoStepValid = computed(
  () => name.value.trim().length > 0 && EMAIL_PATTERN.test(email.value.trim()),
)
const isUsernameStepValid = computed(
  () => isLoginValid.value && loginAvailability.value === 'available',
)
const isPasswordStepValid = computed(() => isPasswordValid.value && isPasswordMatch.value)

const canAdvance = computed(() => {
  if (step.value === 'info') return isInfoStepValid.value
  if (step.value === 'username') return isUsernameStepValid.value
  return isPasswordStepValid.value
})

const goBack = () => {
  const idx = currentStepIndex.value
  if (idx > 0) step.value = FORM_STEPS[idx - 1]
}

// Purely client-side validation errors (never touch the backend), kept
// separate from authStore.errorCode which is reserved for server responses.
const localErrorCode = ref<string | null>(null)
const displayErrorCode = computed(() => localErrorCode.value || authStore.errorCode)

watch([name, email, login, password, confirmPassword], () => {
  localErrorCode.value = null
  if (authStore.errorCode) {
    authStore.clearErrors()
  }
})

const handleSubmit = async () => {
  localErrorCode.value = null

  // On the first two steps, the form's submit event just means "advance"
  // (Enter in a field, or the Next button) — the actual registration call
  // only fires once the password step is reached.
  if (step.value === 'info') {
    if (isInfoStepValid.value) step.value = 'username'
    return
  }
  if (step.value === 'username') {
    if (isUsernameStepValid.value) step.value = 'password'
    return
  }

  if (isLoginTouched.value && !isLoginValid.value) {
    localErrorCode.value = 'VALIDATION_LOGIN_INVALID'
    return
  }
  if (loginAvailability.value === 'taken') {
    localErrorCode.value = 'VALIDATION_LOGIN_TAKEN'
    return
  }
  if (isPasswordTouched.value && !isPasswordValid.value) {
    localErrorCode.value = 'VALIDATION_PASSWORD_INVALID'
    return
  }
  if (confirmPassword.value.length > 0 && !isPasswordMatch.value) {
    localErrorCode.value = 'VALIDATION_PASSWORDS_MISMATCH'
    return
  }

  const outcome = await authStore.register({
    name: name.value.trim(),
    email: email.value.trim(),
    login: login.value.trim(),
    password: password.value,
  })

  if (outcome === 'authenticated') {
    // register() already stores the token (see authStore._handleSuccess),
    // so the user is authenticated at this point — show a confirmation
    // instead of redirecting, and only navigate once they dismiss it.
    step.value = 'success'
  } else if (outcome === 'verification_required') {
    step.value = 'verification'
  }
}

const onContinue = () => {
  router.push({ name: 'Home' })
}
</script>

<template>
  <div class="login-container">
    <div class="login-box">
      <AuthVerificationPanel
        v-if="step === 'verification' && authStore.pendingVerification"
        :title="t('register.verification.title')"
        :subtitle="
          t('register.verification.subtitle', { target: authStore.pendingVerification.target })
        "
        :back-label="t('register.verification.backToLogin')"
        back-to="Login"
      />

      <div v-else-if="step === 'success'" class="success-panel">
        <div class="success-icon" aria-hidden="true">
          <svg
            width="36"
            height="36"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <path d="m9 12 2 2 4-4"></path>
          </svg>
        </div>
        <h2 class="title">{{ $t('register.success.title') }}</h2>
        <p class="subtitle">{{ $t('register.success.subtitle') }}</p>
        <button type="button" class="submit-btn continue-btn" @click="onContinue">
          {{ $t('register.success.continue') }}
        </button>
      </div>

      <template v-else>
        <div class="header">
          <h1 class="title">{{ $t('register.title') }}</h1>
          <p class="subtitle">{{ $t('register.subtitle') }}</p>
        </div>

        <div v-if="displayErrorCode" class="error-message">
          {{ $t(`errors.${displayErrorCode}`, authStore.errorDetails || {}) }}
        </div>

        <form @submit.prevent="handleSubmit" class="form">
          <Transition name="step-fade" mode="out-in">
            <div :key="step" class="step-panel">
              <template v-if="step === 'info'">
                <div class="input-group">
                  <input
                    v-model="name"
                    type="text"
                    :placeholder="$t('register.name_placeholder')"
                    class="input"
                    required
                    autocomplete="name"
                    autofocus
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
              </template>

              <template v-else-if="step === 'username'">
                <div class="input-group">
                  <input
                    v-model="login"
                    type="text"
                    :placeholder="$t('register.login_placeholder')"
                    class="input"
                    :class="{
                      'input-error':
                        (isLoginTouched && !isLoginValid) || loginAvailability === 'taken',
                      'input-success': isLoginValid && loginAvailability === 'available',
                    }"
                    required
                    autocomplete="username"
                    autofocus
                    :disabled="authStore.isLoading"
                    @input="onLoginInput"
                  />
                  <span v-if="loginAvailability === 'checking'" class="login-status">
                    {{ $t('register.login_checking') }}
                  </span>
                  <span
                    v-else-if="loginAvailability === 'available'"
                    class="login-status login-status-success"
                  >
                    {{ $t('register.login_available') }}
                  </span>
                  <span
                    v-else-if="loginAvailability === 'taken'"
                    class="login-status login-status-error"
                  >
                    {{ $t('register.login_taken') }}
                  </span>
                </div>

                <div
                  v-if="isLoginTouched"
                  class="password-rules"
                  role="list"
                  :aria-label="$t('register.loginRulesAriaLabel')"
                >
                  <div
                    v-for="rule in loginRules"
                    :key="rule.id"
                    class="rule-item"
                    :class="{ success: rule.status }"
                    role="listitem"
                  >
                    <span class="rule-icon">{{ rule.status ? '✓' : '○' }}</span>
                    <span class="rule-text">{{ $t(`validation.${rule.label}`) }}</span>
                  </div>
                </div>

                <div v-if="loginSuggestions.length" class="login-suggestions">
                  <span class="login-suggestions-label">{{
                    $t('register.login_suggestions_label')
                  }}</span>
                  <button
                    v-for="suggestion in loginSuggestions"
                    :key="suggestion"
                    type="button"
                    class="login-suggestion-btn"
                    @click="pickLoginSuggestion(suggestion)"
                  >
                    {{ suggestion }}
                  </button>
                </div>
              </template>

              <template v-else-if="step === 'password'">
                <div class="input-group password-group">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    :placeholder="$t('register.password_placeholder')"
                    class="input"
                    :class="{ 'input-error': isPasswordTouched && !isPasswordValid }"
                    required
                    autocomplete="new-password"
                    autofocus
                    :disabled="authStore.isLoading"
                  />
                  <button
                    type="button"
                    class="toggle-password-btn"
                    @click="showPassword = !showPassword"
                    :aria-label="
                      showPassword ? $t('register.hidePassword') : $t('register.showPassword')
                    "
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
                  :aria-label="$t('register.passwordRulesAriaLabel')"
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
              </template>
            </div>
          </Transition>

          <div
            class="step-dots"
            role="tablist"
            :aria-label="
              t('register.stepAriaLabel', {
                current: currentStepIndex + 1,
                total: FORM_STEPS.length,
              })
            "
          >
            <span
              v-for="(s, i) in FORM_STEPS"
              :key="s"
              class="dot"
              :class="{ active: i === currentStepIndex, done: i < currentStepIndex }"
            ></span>
          </div>

          <div class="actions">
            <button
              v-if="currentStepIndex > 0"
              type="button"
              class="back-btn"
              :disabled="authStore.isLoading"
              @click="goBack"
            >
              {{ $t('register.back') }}
            </button>
            <button type="submit" class="submit-btn" :disabled="authStore.isLoading || !canAdvance">
              <span v-if="authStore.isLoading">{{ $t('register.loading') }}</span>
              <span v-else-if="step === 'password'">{{ $t('register.submit') }}</span>
              <span v-else>{{ $t('register.next') }}</span>
            </button>
          </div>
          <div class="create-account">
            <RouterLink to="/login" class="create-link">
              {{ $t('register.already_have_account') }}
            </RouterLink>
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
      </template>
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

.step-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.step-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background-color: var(--color-border);
  transition:
    width 0.25s ease,
    background-color 0.25s ease;
}

.dot.done {
  background-color: var(--color-text-sub);
}

.dot.active {
  width: 22px;
  background-color: var(--color-text-title);
}

.actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
}

.submit-btn {
  flex: 1;
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

.back-btn {
  flex: 0 0 auto;
  padding: 12px 20px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background-color: transparent;
  color: var(--color-text-primary);
  font-weight: 500;
  transition: background-color 0.3s;
}
.back-btn:hover {
  background-color: var(--color-bkg-soft);
}

.success-panel {
  text-align: center;
  padding: 8px 0 4px;
}
.success-icon {
  display: flex;
  justify-content: center;
  color: #22c55e;
  margin-bottom: 16px;
}
.continue-btn {
  width: 100%;
  margin-top: 24px;
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
.back-btn:disabled,
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

.login-status {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-sub);
}

.login-status-success {
  color: #22c55e;
}

.login-status-error {
  color: #ef4444;
}

.login-suggestions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: -6px;
}

.login-suggestions-label {
  font-size: 12px;
  color: var(--color-text-sub);
}

.login-suggestion-btn {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-title);
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.login-suggestion-btn:hover {
  background-color: var(--color-bkg-soft);
}
</style>
