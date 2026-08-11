import { createContext } from 'react'

import type { TokenPair, User } from './types'

export type AuthState = {
  user: User | null
  ready: boolean
  signIn: (tokens: TokenPair) => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthState | null>(null)
