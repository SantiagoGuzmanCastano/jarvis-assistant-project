import { api } from './api'
import type {
  ChatMessage,
  Conversation,
  ConversationDetail,
  ConversationPage,
  ExternalAccount,
  TokenPair,
  User,
  UserSettings,
} from './types'

export const authService = {
  async login(email: string, password: string) {
    const { data } = await api.post<TokenPair>('/auth/login', { email, password })
    return data
  },
  async register(email: string, password: string) {
    await api.post('/auth/register', { email, password })
  },
  async me() {
    const { data } = await api.get<User>('/auth/me')
    return data
  },
  async logout(refreshToken: string) {
    await api.post('/auth/logout', { refresh_token: refreshToken })
  },
}

export const settingsService = {
  async get() {
    const { data } = await api.get<UserSettings>('/user_settings/me')
    return data
  },
  async create(input: Omit<UserSettings, 'user_id'>) {
    const { data } = await api.post<UserSettings>('/user_settings', input)
    return data
  },
  async update(input: Partial<Omit<UserSettings, 'user_id'>>) {
    const { data } = await api.patch<UserSettings>('/user_settings', input)
    return data
  },
  async reset() {
    const { data } = await api.patch<UserSettings>('/user_settings/reset')
    return data
  },
}

export const conversationService = {
  async list(beforeId?: number) {
    const { data } = await api.get<ConversationPage>('/conversations', {
      params: { limit: 10, before_id: beforeId },
    })
    return data
  },
  async create(title?: string) {
    const { data } = await api.post<Conversation>('/conversations', { title })
    return data
  },
  async get(id: number) {
    const { data } = await api.get<ConversationDetail>(`/conversations/${id}`)
    return data
  },
  async rename(id: number, title: string) {
    const { data } = await api.patch<Conversation>(`/conversations/${id}`, { title })
    return data
  },
  async remove(id: number) {
    await api.delete(`/conversations/${id}`)
  },
}

export const chatService = {
  async send(conversationId: number, content: string) {
    const { data } = await api.post<ChatMessage>('/chat/', {
      conversation_id: conversationId,
      content,
    })
    return data
  },
}

export const googleService = {
  async accounts() {
    const { data } = await api.get<ExternalAccount[]>('/external-auth/accounts')
    return data
  },
  async connectUrl() {
    const { data } = await api.get<{ auth_url: string }>('/external-auth/google/connect')
    return data.auth_url
  },
  async disconnect() {
    await api.delete('/external-auth/google')
  },
}
