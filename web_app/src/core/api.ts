import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

import { sessionStore } from './session-store'
import type { ApiErrorBody, TokenPair } from './types'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const api = axios.create({ baseURL })

let refreshInFlight: Promise<TokenPair> | null = null

const isAuthEndpoint = (url?: string) =>
  url?.startsWith('/auth/login') ||
  url?.startsWith('/auth/register') ||
  url?.startsWith('/auth/refresh')

api.interceptors.request.use((config) => {
  const accessToken = sessionStore.read()?.access_token
  if (accessToken && !isAuthEndpoint(config.url)) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined
    const status = error.response?.status
    if (!original || status !== 401 || original._retried || isAuthEndpoint(original.url)) {
      return Promise.reject(error)
    }

    const pair = sessionStore.read()
    if (!pair) return Promise.reject(error)

    original._retried = true
    try {
      refreshInFlight ??= api
        .post<TokenPair>('/auth/refresh', { refresh_token: pair.refresh_token })
        .then(({ data }) => {
          sessionStore.write(data)
          return data
        })
        .finally(() => {
          refreshInFlight = null
        })
      const refreshed = await refreshInFlight
      original.headers.Authorization = `Bearer ${refreshed.access_token}`
      return api(original)
    } catch (refreshError) {
      sessionStore.clear()
      window.dispatchEvent(new Event('jarvis:session-expired'))
      return Promise.reject(refreshError)
    }
  },
)

export function apiErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    return error.response?.data.error?.message ?? fallback
  }
  return fallback
}

export function apiErrorCode(error: unknown) {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    return error.response?.data.error?.code
  }
  return undefined
}
