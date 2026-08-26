import type { AxiosError } from 'axios'
import { ERROR_CODES, isErrorCode } from '@/types/api/errors'

const prefix = 'api' as const
const separator = '.' as const

const formatErrorCode = (separator: string, ...parts: (string | undefined)[]) =>
  parts.filter(Boolean).join(separator)

export interface ServerErrorPayload {
  code?: string
  details?: Record<string, unknown>
}

export function getErrorCode(error: unknown): {
  code: string
  details: Record<string, unknown> | null
} {
  const axiosErr = error as AxiosError<{ error?: ServerErrorPayload; code?: string }>

  const rawCode = axiosErr.response?.data?.error?.code ?? axiosErr.response?.data?.code
  const details = axiosErr.response?.data?.error?.details || null

  if (rawCode && isErrorCode(rawCode)) {
    return { code: formatErrorCode(separator, prefix, rawCode), details }
  }

  if (!axiosErr.response) {
    return { code: formatErrorCode(separator, prefix, ERROR_CODES.NETWORK_ERROR), details: null }
  }

  if (axiosErr.response.status >= 500) {
    return { code: formatErrorCode(separator, prefix, ERROR_CODES.SERVER_ERROR), details: null }
  }

  return { code: formatErrorCode(separator, prefix, ERROR_CODES.UNKNOWN), details: null }
}
