// ai_news_platform/shared/auth/login-rules.json is the canonical
// login/username format contract — read directly here via the "@shared"
// alias (see vite.config.ts), not a copy. The Go side reads the exact same
// file at process init (backend/core/internal/auth/domain/user.go,
// loginRulesPath — it can't go:embed it since shared/ sits outside that Go
// module). The "users_login_format" CHECK constraint in
// sql/auth/migrations/00003_add_user_login.sql mirrors the same pattern and
// is the actual guarantee against a malformed value reaching the database —
// this is only the fail-fast/UX layer on top of it.
import loginRulesSpec from '@shared/auth/login-rules.json'

const MIN_LOGIN_LENGTH = loginRulesSpec.minLength
const MAX_LOGIN_LENGTH = loginRulesSpec.maxLength

export const LOGIN_REGEX = new RegExp(loginRulesSpec.pattern)

const enum LoginRuleId {
  Length = 'length',
  StartsWithLetter = 'startsWithLetter',
  Charset = 'charset',
}

const LOGIN_REQUIREMENTS = {
  LENGTH: 'LOGIN_LENGTH',
  STARTS_WITH_LETTER: 'LOGIN_STARTS_WITH_LETTER',
  CHARSET: 'LOGIN_CHARSET',
} as const

type LoginRequirement = (typeof LOGIN_REQUIREMENTS)[keyof typeof LOGIN_REQUIREMENTS]

export interface LoginRule {
  id: LoginRuleId
  label: LoginRequirement
  test: (value: string) => boolean
}

export interface LoginRuleStatus extends LoginRule {
  status: boolean
}

export const LOGIN_RULES: ReadonlyArray<LoginRule> = [
  {
    id: LoginRuleId.Length,
    label: LOGIN_REQUIREMENTS.LENGTH,
    test: (s) => s.length >= MIN_LOGIN_LENGTH && s.length <= MAX_LOGIN_LENGTH,
  },
  {
    id: LoginRuleId.StartsWithLetter,
    label: LOGIN_REQUIREMENTS.STARTS_WITH_LETTER,
    test: (s) => /^[a-z]/.test(s),
  },
  {
    id: LoginRuleId.Charset,
    label: LOGIN_REQUIREMENTS.CHARSET,
    test: (s) => /^[a-z0-9_]*$/.test(s),
  },
]

export function getLoginValidationStatus(login: string): LoginRuleStatus[] {
  const normalized = login.toLowerCase()
  return LOGIN_RULES.map((rule) => ({
    ...rule,
    status: rule.test(normalized),
  }))
}

export function isLoginFormatValid(login: string): boolean {
  return LOGIN_REGEX.test(login.toLowerCase())
}

// Cyrillic -> Latin transliteration, only what's needed to turn a typical
// display name into a plausible ASCII login suggestion. Not meant to be a
// complete/precise transliteration scheme.
const TRANSLIT_MAP: Record<string, string> = {
  а: 'a',
  б: 'b',
  в: 'v',
  г: 'g',
  д: 'd',
  е: 'e',
  ё: 'e',
  ж: 'zh',
  з: 'z',
  и: 'i',
  й: 'y',
  к: 'k',
  л: 'l',
  м: 'm',
  н: 'n',
  о: 'o',
  п: 'p',
  р: 'r',
  с: 's',
  т: 't',
  у: 'u',
  ф: 'f',
  х: 'h',
  ц: 'ts',
  ч: 'ch',
  ш: 'sh',
  щ: 'sch',
  ъ: '',
  ы: 'y',
  ь: '',
  э: 'e',
  ю: 'yu',
  я: 'ya',
}

function transliterate(value: string): string {
  return value
    .toLowerCase()
    .split('')
    .map((char) => TRANSLIT_MAP[char] ?? char)
    .join('')
}

// Turns a display name into a login suggestion: transliterate, drop
// anything outside [a-z0-9_], collapse repeats, pad/trim to the allowed
// length, and make sure it still starts with a letter.
export function suggestLoginFromName(name: string): string {
  const slug = transliterate(name.trim())
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, MAX_LOGIN_LENGTH)

  const withLetterStart = /^[a-z]/.test(slug) ? slug : `u_${slug}`.slice(0, MAX_LOGIN_LENGTH)

  if (withLetterStart.length >= MIN_LOGIN_LENGTH) return withLetterStart
  return withLetterStart.padEnd(MIN_LOGIN_LENGTH, '0')
}
