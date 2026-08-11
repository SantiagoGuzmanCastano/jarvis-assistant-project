export type TokenPair = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type User = {
  id: number
  email: string
  created_at: string
}

export type UserSettings = {
  user_id: number
  assistant_name: string
  assistant_personality: string
  language_mode: string
}

export type Conversation = {
  id: number
  user_id: number
  title: string
  created_at: string
}

export type ConversationPage = {
  items: Conversation[]
  next_before_id: number | null
  has_more: boolean
}

export type ChatMessage = {
  id?: number
  conversation_id?: number
  role: 'user' | 'assistant'
  content: string
  created_at?: string
}

export type ConversationDetail = Conversation & {
  messages: ChatMessage[]
}

export type ExternalAccount = {
  id: number
  provider: string
  email?: string
  created_at?: string
}

export type ApiErrorBody = {
  error?: {
    code?: string
    message?: string
    details?: unknown
  }
}
