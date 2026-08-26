import type { ChatEvent } from './chat'

export interface ChatStep {
  node: string
  message: string
}

export interface ChatMessage {
  id: string
  backendMessageId?: string | null
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt: string
  reaction?: 'like' | 'dislike' | null
  traceId?: string | null
  steps?: ChatEvent[]
}
