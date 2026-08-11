import type { TokenPair } from './types'

const key = 'jarvis-token-pair'

export const sessionStore = {
  read(): TokenPair | null {
    const persistent = localStorage.getItem(key)
    const legacy = sessionStorage.getItem(key)
    const raw = persistent ?? legacy
    if (!raw) return null
    try {
      const pair = JSON.parse(raw) as TokenPair
      if (!persistent && legacy) {
        localStorage.setItem(key, raw)
        sessionStorage.removeItem(key)
      }
      return pair
    } catch {
      localStorage.removeItem(key)
      sessionStorage.removeItem(key)
      return null
    }
  },
  write(pair: TokenPair) {
    localStorage.setItem(key, JSON.stringify(pair))
    sessionStorage.removeItem(key)
  },
  clear() {
    localStorage.removeItem(key)
    sessionStorage.removeItem(key)
  },
}
