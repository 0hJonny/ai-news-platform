export const API_BASE_URL = 'http://localhost:8080' as string

export const ENDPOINTS = {
  LOGIN: '/auth/login',
  LOGOUT: '/auth/logout',
  REGISTER: '/auth/register',
  ANONIMOUS: '/auth/anonimous',
  USERDATA: '/auth/user',
  LOGIN_AVAILABLE: '/auth/login-available',
  CHECK_USERNAME: '/auth/check-username',
  FEEDBACK: '/agents/chat/feedback',
  STREAM: '/agents/chat/stream',
  SESSION: '/chats/sessions',

  SESSION_TITLE: (id: string) => `/chats/sessions/${id}/title`,
  SESSION_BY_ID: (id: string) => `/chats/sessions/${id}`,
  SESSION_MESSAGES: (id: string) => `/chats/sessions/${id}/messages`,
}
