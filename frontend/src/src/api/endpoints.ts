export const API_BASE_URL = 'http://localhost:8080' as string

export const ENDPOINTS = {
  LOGIN: '/auth/login',
  LOGOUT: '/auth/logout',
  REGISTER: '/auth/register',
  ANONIMOUS: '/auth/anonimous',
  USERDATA: '/auth/user',
  FEEDBACK: '/agents/chat/feedback',
  STREAM: '/agents/chat/stream',
  SESSION: '/chats/sessions',

  SESSION_TITLE: (id: string) => `/chats/sessions/${id}/title`,
  SESSION_BY_ID: (id: string) => `/chats/sessions/${id}`,
  SESSION_MESSAGES: (id: string) => `/chats/sessions/${id}/messages`,

  PUBLICATIONS: '/publications',
  CREATE_PUBLICATION: '/publications',
  PUBLICATIONS_TOTAL: '/publications_total',
  LOANS: '/loans',
  LOANS_TOTAL: '/loans_total',
  READERS: '/readers',
  READERS_TOTAL: '/readers_total',
}
