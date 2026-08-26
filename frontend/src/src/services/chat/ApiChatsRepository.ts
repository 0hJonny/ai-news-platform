import type { AxiosInstance } from 'axios'
import type {
  ChatRequest,
  ChatEvent,
  FinalAnswer,
  FeedbackRequest,
  StreamCallback,
  RepositoryError,
  CreateSessionRequest,
  BackendSession,
  BackendMessage,
} from '@/types/chat/chat'
import { getErrorCode } from '@/utils/errorMapper'
import type { IChatsRepository } from './IChatsRepository'
import { ENDPOINTS } from '@/api/endpoints'

function hasStringError(obj: unknown): obj is { error: string } {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'error' in obj &&
    typeof (obj as Record<string, unknown>).error === 'string'
  )
}

export class ApiChatsRepository implements IChatsRepository {
  constructor(
    private readonly http: AxiosInstance,
    private readonly getToken: () => string | null,
  ) {}

  private async *parseSSEStream(reader: ReadableStreamDefaultReader<Uint8Array>) {
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let currentEvent: { event?: string; data?: string } = {}

    try {
      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          if (buffer.trim() || currentEvent.data) {
            yield this._buildEvent(currentEvent)
          }
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split(/\r?\n/)
        buffer = lines.pop() || ''

        for (const rawLine of lines) {
          const line = rawLine.trimEnd()

          if (line === '') {
            if (currentEvent.data) {
              yield this._buildEvent(currentEvent)
              currentEvent = {}
            }
            continue
          }

          if (line.startsWith(':')) continue

          const colonIndex = line.indexOf(':')
          if (colonIndex === -1) continue

          const field = line.slice(0, colonIndex)
          const fieldValue = line.slice(colonIndex + 1).replace(/^ /, '')

          if (field === 'event') {
            currentEvent.event = fieldValue
          } else if (field === 'data') {
            currentEvent.data = currentEvent.data
              ? `${currentEvent.data}\n${fieldValue}`
              : fieldValue
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  private _buildEvent(event: { event?: string; data?: string }) {
    if (!event.data) return null
    try {
      return {
        type: event.event || 'message',
        data: JSON.parse(event.data),
      }
    } catch (e) {
      console.warn('[SSE] Failed to parse JSON:', event.data, e)
      return null
    }
  }

  async streamChat(
    request: ChatRequest,
    onEvent: StreamCallback,
    signal?: AbortSignal,
  ): Promise<{ success: true; data: FinalAnswer } | { success: false; error: RepositoryError }> {
    try {
      const token = this.getToken()
      const baseUrl = this.http.defaults.baseURL?.replace(/\/$/, '') || ''

      const response = await fetch(`${baseUrl}${ENDPOINTS.STREAM}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(request),
        signal,
      })

      if (!response.ok || !response.body) {
        const errorText = await response.text().catch(() => 'Unknown error')
        return {
          success: false,
          error: {
            code: 'HTTP_ERROR',
            message: `Server error ${response.status}: ${errorText}`,
          },
        }
      }

      const reader = response.body.getReader()
      let finalAnswer: FinalAnswer | null = null

      for await (const parsed of this.parseSSEStream(reader)) {
        if (!parsed) continue

        const { type, data } = parsed

        if (type !== 'final' && 'node' in data && 'message' in data) {
          onEvent(data as ChatEvent)
        } else if (type === 'final' && 'answer' in data && 'session_id' in data) {
          finalAnswer = data as FinalAnswer
          onEvent(finalAnswer)
        }
      }

      if (!finalAnswer) {
        return {
          success: false,
          error: { code: 'NO_FINAL_ANSWER', message: 'Stream ended without final answer' },
        }
      }

      return { success: true, data: finalAnswer }
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return { success: false, error: { code: 'ABORTED', message: 'Request cancelled by user' } }
      }

      const errorMessage = err instanceof Error ? err.message : String(err)
      return {
        success: false,
        error: {
          code:
            errorMessage.includes('Network') || errorMessage.includes('fetch')
              ? 'NETWORK_ERROR'
              : 'UNKNOWN_ERROR',
          message: errorMessage,
        },
      }
    }
  }

  private async _execute<T>(
    method: 'get' | 'post' | 'put' | 'delete',
    endpoint: string,
    payload?: unknown,
  ): Promise<{ success: true; data: T } | { success: false; error: RepositoryError }> {
    try {
      const response = await this.http[method]<T>(endpoint, payload)
      return { success: true, data: response.data }
    } catch (e: unknown) {
      const { code, details } = getErrorCode(e)

      let errorMessage = 'Ошибка запроса к чатам'
      if (hasStringError(details)) {
        errorMessage = details.error
      }

      const safeDetails =
        typeof details === 'object' && details !== null
          ? (details as Record<string, unknown>)
          : undefined

      return {
        success: false,
        error: {
          code: code || 'CHAT_HTTP_ERROR',
          message: errorMessage,
          details: safeDetails,
        },
      }
    }
  }

  async createSession(request: CreateSessionRequest) {
    return this._execute<BackendSession>('post', ENDPOINTS.SESSION, request)
  }

  async getSessions() {
    return this._execute<BackendSession[]>('get', ENDPOINTS.SESSION)
  }

  async updateSessionTitle(id: string, title: string) {
    return this._execute<void>('put', ENDPOINTS.SESSION_TITLE(id), { title })
  }

  async deleteSession(id: string) {
    return this._execute<void>('delete', ENDPOINTS.SESSION_BY_ID(id))
  }

  async getSessionMessages(id: string) {
    return this._execute<BackendMessage[]>('get', ENDPOINTS.SESSION_MESSAGES(id))
  }

  async sendFeedback(
    request: FeedbackRequest,
  ): Promise<{ success: true } | { success: false; error: RepositoryError }> {
    try {
      await this.http.post(ENDPOINTS.FEEDBACK, request)
      return { success: true }
    } catch (e: unknown) {
      const { code, details } = getErrorCode(e)

      let errorMessage = 'Ошибка отправки отзыва'
      if (hasStringError(details)) {
        errorMessage = details.error
      }

      const safeDetails =
        typeof details === 'object' && details !== null
          ? (details as Record<string, unknown>)
          : undefined

      return {
        success: false,
        error: {
          code: code || 'FEEDBACK_ERROR',
          message: errorMessage,
          details: safeDetails,
        },
      }
    }
  }
}
