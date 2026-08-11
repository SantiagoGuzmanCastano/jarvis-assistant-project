import { useEffect, useId, useState, type FormEvent, type KeyboardEvent } from 'react'

import { apiErrorMessage } from '../../core/api'
import { authService } from '../../core/services'
import { useAuth } from '../../core/use-auth'
import { ConstellationBackground } from './ConstellationBackground'

const introTitles = [
  'Tu centro de control, en una conversación.',
  'Menos pestañas. Más claridad.',
  'Lo importante, al alcance de una pregunta.',
  'Una conversación para ordenar tu día.',
  'Piensa menos en tareas. Avanza más.',
  'Tu contexto, reunido en un solo lugar.',
  'Empieza por una idea. Jarvis sigue contigo.',
  'Una forma más simple de mantener el rumbo.',
  'Convierte pendientes en próximos pasos.',
  'Un espacio tranquilo para hacer más.',
] as const

function nextIntroTitle() {
  const previousIndex = Number(sessionStorage.getItem('jarvis-intro-title-index') ?? '-1')
  const nextIndex = (previousIndex + 1) % introTitles.length
  sessionStorage.setItem('jarvis-intro-title-index', String(nextIndex))
  return introTitles[nextIndex]
}

export function AuthPage() {
  const { signIn } = useAuth()
  const emailId = useId()
  const passwordId = useId()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [introTitle] = useState(nextIntroTitle)
  const [typedTitle, setTypedTitle] = useState('')
  const isLogin = mode === 'login'

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setTypedTitle(introTitle)
      return
    }
    let position = 0
    const timer = window.setInterval(() => {
      position += 1
      setTypedTitle(introTitle.slice(0, position))
      if (position === introTitle.length) window.clearInterval(timer)
    }, 24)
    return () => window.clearInterval(timer)
  }, [introTitle])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    if (!email.includes('@')) return setError('Escribe un email válido.')
    if (password.length < 8 || password.length > 25) {
      return setError('La contraseña debe tener entre 8 y 25 caracteres.')
    }
    setPending(true)
    try {
      if (isLogin) {
        await signIn(await authService.login(email.trim(), password))
      } else {
        await authService.register(email.trim(), password)
        setMode('login')
        setPassword('')
        setNotice('Cuenta creada. Inicia sesión para entrar a Jarvis.')
      }
    } catch (requestError) {
      setError(apiErrorMessage(requestError, 'No se pudo completar la solicitud.'))
    } finally {
      setPending(false)
    }
  }

  function switchMode(nextMode: 'login' | 'register') {
    if (pending || nextMode === mode) return
    setMode(nextMode)
    setError(null)
    setNotice(null)
    setPassword('')
    setPasswordVisible(false)
  }

  function moveModeFocus(event: KeyboardEvent<HTMLButtonElement>, nextMode: 'login' | 'register') {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
    event.preventDefault()
    switchMode(nextMode)
    requestAnimationFrame(() => document.getElementById(`auth-${nextMode}`)?.focus())
  }

  return (
    <main className="auth-page">
      <ConstellationBackground />
      <div className="auth-layout">
        <section className="auth-intro" aria-labelledby="auth-intro-title">
          <div className="brand auth-brand"><span className="brand-mark" />Jarvis</div>
          <div className="auth-intro-copy">
            <p className="eyebrow">Asistente personal</p>
            <h1 id="auth-intro-title" aria-label={introTitle}><span aria-hidden="true">{typedTitle}</span><span className="typing-cursor" aria-hidden="true" /></h1>
            <p>Un espacio claro para pensar, conversar y trabajar con Jarvis.</p>
          </div>
          <p className="auth-signal">Sesión segura · Gmail y Calendar solo cuando los autorizas</p>
        </section>

        <section className="auth-panel" aria-labelledby="auth-title">
          <div className="auth-panel-header">
            <p className="eyebrow">{isLogin ? 'Acceso' : 'Registro'}</p>
            <h2 id="auth-title">{isLogin ? 'Bienvenido de nuevo' : 'Crea tu cuenta'}</h2>
            <p className="muted">
              {isLogin ? 'Inicia sesión para continuar con Jarvis.' : 'Configura tu asistente en unos minutos.'}
            </p>
          </div>

          <div className="auth-mode" role="tablist" aria-label="Tipo de acceso">
            <button id="auth-login" role="tab" aria-selected={isLogin} aria-controls="auth-form" tabIndex={isLogin ? 0 : -1} className={isLogin ? 'active' : ''} onClick={() => switchMode('login')} onKeyDown={(event) => moveModeFocus(event, 'register')}>Iniciar sesión</button>
            <button id="auth-register" role="tab" aria-selected={!isLogin} aria-controls="auth-form" tabIndex={isLogin ? -1 : 0} className={!isLogin ? 'active' : ''} onClick={() => switchMode('register')} onKeyDown={(event) => moveModeFocus(event, 'login')}>Crear cuenta</button>
          </div>

          <form id="auth-form" onSubmit={submit} className="auth-form" noValidate>
            <div className="field-group">
              <label htmlFor={emailId}>Email</label>
              <input id={emailId} type="email" autoComplete="email" autoFocus value={email} disabled={pending} onChange={(event) => setEmail(event.target.value)} aria-invalid={Boolean(error && !email.includes('@'))} />
            </div>
            <div className="field-group">
              <div className="field-label-row"><label htmlFor={passwordId}>Contraseña</label>{!isLogin && <span>8–25 caracteres</span>}</div>
              <div className="password-input"><input id={passwordId} type={passwordVisible ? 'text' : 'password'} autoComplete={isLogin ? 'current-password' : 'new-password'} value={password} disabled={pending} onChange={(event) => setPassword(event.target.value)} aria-invalid={Boolean(error && password.length > 0 && (password.length < 8 || password.length > 25))} /><button type="button" onClick={() => setPasswordVisible((visible) => !visible)} disabled={pending} aria-label={passwordVisible ? 'Ocultar contraseña' : 'Mostrar contraseña'}>{passwordVisible ? 'Ocultar' : 'Mostrar'}</button></div>
            </div>
            <div className="auth-feedback" aria-live="polite">{error && <p className="form-error" role="alert">{error}</p>}{notice && <p className="notice" role="status">{notice}</p>}</div>
            <button className="primary-button auth-submit" disabled={pending} aria-busy={pending}>
              {pending && <span className="button-spinner" aria-hidden="true" />}{pending ? 'Procesando…' : isLogin ? 'Entrar a Jarvis' : 'Crear cuenta'}
            </button>
          </form>

          <p className="auth-footnote">Al continuar, usas una sesión renovable y segura para tu cuenta.</p>
        </section>
      </div>
    </main>
  )
}
