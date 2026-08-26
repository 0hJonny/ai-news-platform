export type UUID = string

export interface ChatRequest {
  session_id: string // UUID
  question: string
}

export interface ChatEvent {
  node: string
  message: string
  model?: string | null
}

export interface FinalAnswer {
  session_id: string
  answer: string
  trace_id?: string | null
  message_id?: string | null // UUID from the backend DB
}

export interface FeedbackRequest {
  message_id: string // Required UUID of the message from the DB
  trace_id?: string | null
  rating: 'like' | 'dislike'
  comment?: string | null
}

// Type for the streaming callback
export type StreamCallback = (event: ChatEvent | FinalAnswer) => void

// Repository error type (shared across all methods)
export interface RepositoryError {
  code: string
  message: string
  details?: Record<string, unknown>
  status?: number
}

export interface BackendSession {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  deleted_at?: string | null
}

export interface BackendMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  trace_id?: string | null
  parent_id?: string | null
  // rating?: 'like' | 'dislike' | null
}

// Creation request
export interface CreateSessionRequest {
  title: string
}
