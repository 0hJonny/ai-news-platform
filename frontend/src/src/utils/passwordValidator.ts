const MIN_PASSWORD_LENGTH = 8

const REGEX_UPPER = /[A-Z]/
const REGEX_LOWER = /[a-z]/
const REGEX_DIGIT = /\d/
const REGEX_SPECIAL = /[!@#$%^&*(),.?":{}|<>_+=\-/\\|~`[\]]/

const enum PasswordRuleId {
  Length = 'length',
  Upper = 'upper',
  Lower = 'lower',
  Digit = 'digit',
  Special = 'special',
}

const PASSWORD_REQUIREMENTS = {
  MIN_LENGTH: 'PASS_MIN_LENGTH',
  UPPERCASE: 'PASS_UPPERCASE',
  LOWERCASE: 'PASS_LOWERCASE',
  DIGIT: 'PASS_NUMBER',
  SPECIAL_CHAR: 'PASS_SPECIAL_CHAR',
} as const

type PasswordRequirement = (typeof PASSWORD_REQUIREMENTS)[keyof typeof PASSWORD_REQUIREMENTS]

export interface PasswordRule {
  id: PasswordRuleId
  label: PasswordRequirement
  test: (value: string) => boolean
}

export interface PasswordRuleStatus extends PasswordRule {
  status: boolean
}

export const PASSWORD_RULES: ReadonlyArray<PasswordRule> = [
  {
    id: PasswordRuleId.Length,
    label: PASSWORD_REQUIREMENTS.MIN_LENGTH,
    test: (s) => s.length >= MIN_PASSWORD_LENGTH,
  },
  {
    id: PasswordRuleId.Upper,
    label: PASSWORD_REQUIREMENTS.UPPERCASE,
    test: (s) => REGEX_UPPER.test(s),
  },
  {
    id: PasswordRuleId.Lower,
    label: PASSWORD_REQUIREMENTS.LOWERCASE,
    test: (s) => REGEX_LOWER.test(s),
  },
  {
    id: PasswordRuleId.Digit,
    label: PASSWORD_REQUIREMENTS.DIGIT,
    test: (s) => REGEX_DIGIT.test(s),
  },
  {
    id: PasswordRuleId.Special,
    label: PASSWORD_REQUIREMENTS.SPECIAL_CHAR,
    test: (s) => REGEX_SPECIAL.test(s),
  },
]

export function getPasswordValidationStatus(password: string): PasswordRuleStatus[] {
  return PASSWORD_RULES.map((rule) => ({
    ...rule,
    status: rule.test(password),
  }))
}

export function isPasswordCompliant(password: string): boolean {
  return PASSWORD_RULES.every((rule) => rule.test(password))
}
