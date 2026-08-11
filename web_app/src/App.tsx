import { AuthPage } from './features/auth/AuthPage'
import { ConstellationBackground } from './features/auth/ConstellationBackground'
import { AppShell } from './features/app/AppShell'
import { useAuth } from './core/use-auth'

export default function App() {
  const { ready, user } = useAuth()
  if (!ready) {
    return (
      <main className="auth-page auth-loading-page">
        <ConstellationBackground />
        <div className="auth-loading-panel">
          <span className="loader" />
          <p>Comprobando sesión…</p>
        </div>
      </main>
    )
  }
  return user ? <AppShell /> : <AuthPage />
}
