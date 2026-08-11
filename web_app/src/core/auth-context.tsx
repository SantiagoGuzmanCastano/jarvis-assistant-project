import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { authService } from './services'
import { sessionStore } from './session-store'
import type { TokenPair, User } from './types'
import { AuthContext } from './auth-state'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  const clearSession = useCallback(() => {
    sessionStore.clear()
    setUser(null)
  }, [])

  const loadUser = useCallback(async () => {
    if (!sessionStore.read()) {
      setReady(true)
      return
    }
    try {
      setUser(await authService.me())
    } catch {
      clearSession()
    } finally {
      setReady(true)
    }
  }, [clearSession])

  useEffect(() => {
    void loadUser()
    window.addEventListener('jarvis:session-expired', clearSession)
    return () => window.removeEventListener('jarvis:session-expired', clearSession)
  }, [clearSession, loadUser])

  const signIn = useCallback(async (tokens: TokenPair) => {
    sessionStore.write(tokens)
    setUser(await authService.me())
  }, [])

  const signOut = useCallback(async () => {
    const pair = sessionStore.read()
    try {
      if (pair) await authService.logout(pair.refresh_token)
    } finally {
      clearSession()
    }
  }, [clearSession])

  const value = useMemo(
    () => ({ user, ready, signIn, signOut }),
    [ready, signIn, signOut, user],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
