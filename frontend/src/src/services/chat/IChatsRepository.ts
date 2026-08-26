import type {
  ChatRequest,
  FinalAnswer,
  FeedbackRequest,
  StreamCallback,
  RepositoryError,
  BackendSession,
  CreateSessionRequest,
  BackendMessage,
} from '@/types/chat/chat'

export interface IChatsRepository {
  streamChat(
    request: ChatRequest,
    onEvent: StreamCallback,
    signal?: AbortSignal,
  ): Promise<{ success: true; data: FinalAnswer } | { success: false; error: RepositoryError }>
  sendFeedback(
    request: FeedbackRequest,
  ): Promise<{ success: true } | { success: false; error: RepositoryError }>

  createSession(
    request: CreateSessionRequest,
  ): Promise<{ success: true; data: BackendSession } | { success: false; error: RepositoryError }>
  getSessions(): Promise<
    { success: true; data: BackendSession[] } | { success: false; error: RepositoryError }
  >
  updateSessionTitle(
    id: string,
    title: string,
  ): Promise<{ success: true } | { success: false; error: RepositoryError }>
  deleteSession(id: string): Promise<{ success: true } | { success: false; error: RepositoryError }>
  getSessionMessages(
    id: string,
  ): Promise<{ success: true; data: BackendMessage[] } | { success: false; error: RepositoryError }>
}
