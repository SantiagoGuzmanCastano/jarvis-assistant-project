import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'

import { apiErrorCode, apiErrorMessage } from '../../core/api'
import { useAuth } from '../../core/use-auth'
import { chatService, conversationService, googleService, settingsService } from '../../core/services'
import type { ChatMessage, Conversation, ConversationDetail, UserSettings } from '../../core/types'
import { ThinkingGame } from './ThinkingGame'

type View = 'chat' | 'settings' | 'google'

export function AppShell() {
  const { user, signOut } = useAuth()
  const queryClient = useQueryClient()
  const [view, setView] = useState<View>('chat')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [visibleConversations, setVisibleConversations] = useState<Conversation[]>([])
  const [loadedPageSizes, setLoadedPageSizes] = useState<number[]>([])
  const [nextBeforeId, setNextBeforeId] = useState<number | null>(null)
  const [hasMoreConversations, setHasMoreConversations] = useState(false)

  const settingsQuery = useQuery({ queryKey: ['settings'], queryFn: settingsService.get, retry: false })
  const conversationsQuery = useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationService.list(),
  })

  useEffect(() => {
    if (!conversationsQuery.data) return
    setVisibleConversations(conversationsQuery.data.items)
    setLoadedPageSizes([conversationsQuery.data.items.length])
    setNextBeforeId(conversationsQuery.data.next_before_id)
    setHasMoreConversations(conversationsQuery.data.has_more)
  }, [conversationsQuery.data])

  const createConversation = useMutation({
    mutationFn: () => conversationService.create(),
    onSuccess: (conversation) => {
      setVisibleConversations((current) => [conversation, ...current])
      setLoadedPageSizes((current) => current.length ? [current[0] + 1, ...current.slice(1)] : [1])
      setSelectedId(conversation.id)
      setView('chat')
      setMobileOpen(false)
    },
  })

  const loadMoreConversations = useMutation({
    mutationFn: () => conversationService.list(nextBeforeId ?? undefined),
    onSuccess: (page) => {
      setVisibleConversations((current) => [
        ...current,
        ...page.items.filter((item) => !current.some((existing) => existing.id === item.id)),
      ])
      setLoadedPageSizes((current) => [...current, page.items.length])
      setNextBeforeId(page.next_before_id)
      setHasMoreConversations(page.has_more)
    },
  })

  const shownConversations = visibleConversations
  const hasNoConversations = !conversationsQuery.isLoading
    && !conversationsQuery.isError
    && shownConversations.length === 0
  const shouldChooseConversation = !conversationsQuery.isLoading
    && !conversationsQuery.isError
    && shownConversations.length > 0
    && selectedId === null

  useEffect(() => {
    if (selectedId !== null && !shownConversations.some((conversation) => conversation.id === selectedId)) {
      setSelectedId(null)
    }
  }, [selectedId, shownConversations])

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get('google_connected') === '1') {
      queryClient.invalidateQueries({ queryKey: ['google-accounts'] })
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [queryClient])

  if (settingsQuery.isLoading) return <PageLoader label="Preparando Jarvis…" />
  if (settingsQuery.isError && apiErrorCode(settingsQuery.error) === 'user_settings_not_found') {
    return <Onboarding onCreated={() => queryClient.invalidateQueries({ queryKey: ['settings'] })} />
  }
  if (settingsQuery.isError) return <PageError message={apiErrorMessage(settingsQuery.error, 'No se pudieron cargar los ajustes.')} onRetry={() => settingsQuery.refetch()} />
  if (!user || !settingsQuery.data) return null

  const chooseConversation = (id: number) => {
    setSelectedId(id)
    setView('chat')
    setMobileOpen(false)
  }

  const loadLessConversations = () => {
    if (loadedPageSizes.length <= 1) return
    const lastPageSize = loadedPageSizes.at(-1) ?? 0
    const reducedConversations = visibleConversations.slice(
      0,
      Math.max(0, visibleConversations.length - lastPageSize),
    )
    setVisibleConversations(reducedConversations)
    setLoadedPageSizes((current) => current.slice(0, -1))
    setNextBeforeId(reducedConversations.at(-1)?.id ?? null)
    setHasMoreConversations(true)
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-top">
          <div className="brand"><span className="brand-mark" />Jarvis AI</div>
          <button className="new-chat" onClick={() => createConversation.mutate()} disabled={createConversation.isPending}>+ Nueva conversación</button>
        </div>
        <p className="sidebar-section-label">Conversaciones</p>
        <nav className="conversation-list" aria-label="Conversaciones">
          {conversationsQuery.isLoading && <p className="muted">Cargando conversaciones…</p>}
          {conversationsQuery.isError && <button className="text-button" onClick={() => conversationsQuery.refetch()}>Reintentar conversaciones</button>}
          {!conversationsQuery.isLoading && !shownConversations.length && <p className="muted">Aún no tienes conversaciones.</p>}
          {shownConversations.map((conversation) => <ConversationItem key={conversation.id} conversation={conversation} selected={view === 'chat' && selectedId === conversation.id} onChoose={() => chooseConversation(conversation.id)} onRenamed={() => conversationsQuery.refetch()} onDeleted={() => { if (selectedId === conversation.id) setSelectedId(null); conversationsQuery.refetch() }} />)}
          {hasMoreConversations && <button className="text-button" onClick={() => loadMoreConversations.mutate()} disabled={loadMoreConversations.isPending}>{loadMoreConversations.isPending ? 'Cargando…' : 'Cargar más'}</button>}
          {loadedPageSizes.length > 1 && <button className="text-button" onClick={loadLessConversations}>Cargar menos</button>}
        </nav>
        <div className="sidebar-bottom">
          <button className={view === 'settings' ? 'nav-item selected' : 'nav-item'} onClick={() => { setView('settings'); setMobileOpen(false) }}><span aria-hidden="true">⚙</span>Ajustes</button>
          <button className="nav-item" onClick={() => void signOut()}><span aria-hidden="true">↗</span>Cerrar sesión</button>
          <div className="user-summary"><span className="user-avatar" aria-hidden="true">{user.email[0].toUpperCase()}</span><div><strong>{user.email.split('@')[0]}</strong><p>{user.email}</p></div></div>
        </div>
      </aside>
      {mobileOpen && <button aria-label="Cerrar menú" className="backdrop" onClick={() => setMobileOpen(false)} />}
      <main className="app-main">
        <header className="topbar"><button className="menu-button" onClick={() => setMobileOpen(true)} aria-label="Abrir conversaciones">☰</button><span>{view === 'chat' ? 'Conversaciones' : view === 'settings' ? 'Ajustes' : 'Cuenta Google'}</span></header>
        {view === 'chat' && conversationsQuery.isLoading ? <PageLoader label="Cargando conversaciones…" /> : null}
        {view === 'chat' && conversationsQuery.isError ? <PageError message={apiErrorMessage(conversationsQuery.error, 'No se pudieron cargar las conversaciones.')} onRetry={() => conversationsQuery.refetch()} /> : null}
        {view === 'chat' && hasNoConversations ? <NoConversations onCreate={() => createConversation.mutate()} creating={createConversation.isPending} /> : null}
        {view === 'chat' && shouldChooseConversation ? <ConversationWelcome onCreate={() => createConversation.mutate()} creating={createConversation.isPending} /> : null}
        {view === 'chat' && !conversationsQuery.isLoading && !conversationsQuery.isError && !hasNoConversations && !shouldChooseConversation && <ChatPanel conversationId={selectedId} settings={settingsQuery.data} />}
        {view === 'settings' && <SettingsPanel settings={settingsQuery.data} onGoogle={() => setView('google')} />}
        {view === 'google' && <GooglePanel onBack={() => setView('settings')} />}
      </main>
    </div>
  )
}

function ConversationItem({ conversation, selected, onChoose, onRenamed, onDeleted }: { conversation: Conversation; selected: boolean; onChoose: () => void; onRenamed: () => void; onDeleted: () => void }) {
  const rename = useMutation({ mutationFn: (title: string) => conversationService.rename(conversation.id, title), onSuccess: onRenamed })
  const remove = useMutation({ mutationFn: () => conversationService.remove(conversation.id), onSuccess: onDeleted })
  return <div className={`conversation-item ${selected ? 'selected' : ''}`}><button onClick={onChoose}>{conversation.title}</button><details><summary aria-label={`Acciones para ${conversation.title}`}>⋮</summary><div className="conversation-actions"><button onClick={() => { const title = window.prompt('Nuevo nombre', conversation.title); if (title?.trim()) rename.mutate(title.trim()) }}>Renombrar</button><button className="danger-text" onClick={() => { if (window.confirm(`¿Eliminar “${conversation.title}”? Esta acción no se puede deshacer.`)) remove.mutate() }}>Eliminar</button></div></details></div>
}

function ChatPanel({ conversationId, settings }: { conversationId: number | null; settings: UserSettings }) {
  const queryClient = useQueryClient()
  const [content, setContent] = useState('')
  const [sendError, setSendError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const composerRef = useRef<HTMLTextAreaElement>(null)
  const sendRequestRef = useRef(0)
  const detailQuery = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => conversationService.get(conversationId!),
    enabled: conversationId !== null,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  })
  const send = useMutation({
    mutationFn: (message: string) => chatService.send(conversationId!, message),
    onMutate: async (message) => {
      setSendError(null)
      const requestId = ++sendRequestRef.current
      await queryClient.cancelQueries({ queryKey: ['conversation', conversationId] })
      const previousConversation = queryClient.getQueryData<ConversationDetail>(['conversation', conversationId])
      const optimistic: ChatMessage = { role: 'user', content: message }
      queryClient.setQueryData<ConversationDetail>(['conversation', conversationId], (current) => current ? { ...current, messages: [...current.messages, optimistic] } : current)
      return { previousConversation, requestId }
    },
    onSuccess: async (reply, _message, context) => {
      queryClient.setQueryData<ConversationDetail>(['conversation', conversationId], (current) => current ? { ...current, messages: [...current.messages, reply] } : current)
      void queryClient.invalidateQueries({ queryKey: ['conversations'] })
      try {
        const confirmedConversation = await conversationService.get(conversationId!)
        if (context?.requestId === sendRequestRef.current) {
          queryClient.setQueryData(['conversation', conversationId], confirmedConversation)
        }
      } catch {
        // Conserva el mensaje optimista y la respuesta hasta la siguiente lectura correcta.
      }
    },
    onError: (error, _message, context) => {
      if (context?.requestId === sendRequestRef.current && context.previousConversation) {
        queryClient.setQueryData(['conversation', conversationId], context.previousConversation)
      }
      setSendError(apiErrorMessage(error, 'No se pudo enviar el mensaje.'))
    },
  })
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [detailQuery.data, send.isPending])
  function resizeComposer(textarea: HTMLTextAreaElement) {
    const maximumHeight = 160
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, maximumHeight)}px`
    textarea.style.overflowY = textarea.scrollHeight > maximumHeight ? 'auto' : 'hidden'
  }
  function submit(event: FormEvent) { event.preventDefault(); const message = content.trim(); if (!message || send.isPending) return; setContent(''); requestAnimationFrame(() => { if (composerRef.current) resizeComposer(composerRef.current) }); send.mutate(message) }
  if (conversationId === null) return <EmptyState title="Selecciona o crea una conversación" description="Tu historial y las respuestas de Jarvis aparecerán aquí." />
  if (detailQuery.isLoading) return <PageLoader label="Cargando conversación…" />
  if (detailQuery.isError) return <PageError message={apiErrorMessage(detailQuery.error, 'No se pudo cargar esta conversación.')} onRetry={() => detailQuery.refetch()} />
  const messages = [...(detailQuery.data?.messages ?? [])].sort((first, second) => {
    const firstTime = first.created_at ? Date.parse(first.created_at) : Number.MAX_SAFE_INTEGER
    const secondTime = second.created_at ? Date.parse(second.created_at) : Number.MAX_SAFE_INTEGER
    if (firstTime !== secondTime) return firstTime - secondTime
    if (first.id !== undefined && second.id !== undefined) return first.id - second.id
    if (first.id !== undefined) return -1
    if (second.id !== undefined) return 1
    return 0
  })
  return <section className="chat-panel"><div className="chat-heading"><p className="eyebrow">{settings.assistant_name}</p><h1>{detailQuery.data?.title}</h1></div><div className="messages" aria-live="polite">{!messages.length && <EmptyState title={`Habla con ${settings.assistant_name}`} description="Puedes preguntarle por tus correos, consultar tu calendario o iniciar cualquier conversación." />}{messages.map((message, index) => <article className={`message ${message.role}`} key={`${message.id ?? 'pending'}-${index}`}><div className="message-content"><ReactMarkdown>{message.content}</ReactMarkdown></div></article>)}{send.isPending && <ThinkingGame assistantName={settings.assistant_name} />}{sendError && <div className="inline-error">{sendError}<button onClick={() => detailQuery.refetch()}>Reintentar</button></div>}<div ref={bottomRef} /></div><form className="composer" onSubmit={submit}><textarea ref={composerRef} value={content} onChange={(event) => setContent(event.target.value)} onInput={(event) => resizeComposer(event.currentTarget)} placeholder="Chatea ahora" rows={1} disabled={send.isPending} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} /><button className="send-button" disabled={!content.trim() || send.isPending} aria-label="Enviar mensaje">↑</button></form></section>
}

function Onboarding({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState('Jarvis'); const [personality, setPersonality] = useState('Leal, útil y directo.'); const [language, setLanguage] = useState('auto'); const create = useMutation({ mutationFn: () => settingsService.create({ assistant_name: name, assistant_personality: personality, language_mode: language }), onSuccess: onCreated })
  return <main className="onboarding"><section className="settings-card"><p className="eyebrow">Primer paso</p><h1>Personaliza tu asistente</h1><p className="muted">Estas preferencias pertenecen a tu cuenta y cambian cómo Jarvis conversa contigo.</p><label>Nombre del asistente<input value={name} onChange={(event) => setName(event.target.value)} /></label><label>Personalidad<textarea value={personality} onChange={(event) => setPersonality(event.target.value)} rows={3} /></label><label>Idioma<select value={language} onChange={(event) => setLanguage(event.target.value)}><option value="auto">Automático</option><option value="es">Español</option><option value="en">English</option></select></label>{create.isError && <p className="form-error">{apiErrorMessage(create.error, 'No se pudieron guardar los ajustes.')}</p>}<button className="primary-button" onClick={() => create.mutate()} disabled={create.isPending}>{create.isPending ? 'Guardando…' : 'Continuar'}</button></section></main>
}

function SettingsPanel({ settings, onGoogle }: { settings: UserSettings; onGoogle: () => void }) {
  const queryClient = useQueryClient(); const [name, setName] = useState(settings.assistant_name); const [personality, setPersonality] = useState(settings.assistant_personality); const [language, setLanguage] = useState(settings.language_mode); const save = useMutation({ mutationFn: () => settingsService.update({ assistant_name: name, assistant_personality: personality, language_mode: language }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings'] }) }); const reset = useMutation({ mutationFn: settingsService.reset, onSuccess: (data) => { setName(data.assistant_name); setPersonality(data.assistant_personality); setLanguage(data.language_mode); queryClient.invalidateQueries({ queryKey: ['settings'] }) } })
  return <section className="settings-page"><div className="page-heading"><p className="eyebrow">Preferencias</p><h1>Personaliza tu experiencia</h1><p className="muted">Define cómo Jarvis se presenta y se comunica contigo.</p></div><div className="settings-card"><h2>Asistente</h2><label>Nombre del asistente<input value={name} onChange={(event) => setName(event.target.value)} /></label><label>Personalidad<textarea value={personality} onChange={(event) => setPersonality(event.target.value)} rows={4} /></label><label>Idioma<select value={language} onChange={(event) => setLanguage(event.target.value)}><option value="auto">Automático</option><option value="es">Español</option><option value="en">English</option></select></label>{save.isError && <p className="form-error">{apiErrorMessage(save.error, 'No se pudieron guardar los cambios.')}</p>}<button className="primary-button" onClick={() => save.mutate()} disabled={save.isPending}>{save.isPending ? 'Guardando…' : 'Guardar cambios'}</button></div><div className="settings-card"><h2>Conexiones</h2><button className="navigation-row" onClick={onGoogle}><span><b>Cuenta Google</b><small>Conectar o desconectar Gmail y Calendar</small></span><span>›</span></button></div><div className="settings-card"><h2>Mantenimiento</h2><button className="secondary-button" onClick={() => { if (window.confirm('¿Restablecer nombre, personalidad e idioma?')) reset.mutate() }} disabled={reset.isPending}>Restablecer valores por defecto</button></div></section>
}

function GooglePanel({ onBack }: { onBack: () => void }) {
  const queryClient = useQueryClient(); const accounts = useQuery({ queryKey: ['google-accounts'], queryFn: googleService.accounts, retry: false }); const connect = useMutation({ mutationFn: googleService.connectUrl, onSuccess: (url) => window.location.assign(url) }); const disconnect = useMutation({ mutationFn: googleService.disconnect, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['google-accounts'] }) }); const noAccount = apiErrorCode(accounts.error) === 'external_accounts_not_found'; const connected = !accounts.isError && (accounts.data?.some((account) => account.provider === 'google') ?? false)
  return <section className="settings-page"><button className="text-button back-button" onClick={onBack}>← Volver a ajustes</button><div className="page-heading"><p className="eyebrow">Integración</p><h1>Cuenta Google</h1><p className="muted">Gmail y Calendar solo se usan cuando autorizas una cuenta de Google.</p></div><div className="settings-card"><div className="status-line"><span className={connected ? 'status-dot connected' : 'status-dot'} />{accounts.isLoading ? 'Comprobando conexión…' : connected ? 'Cuenta conectada' : 'Sin cuenta conectada'}</div>{accounts.isError && !noAccount && <p className="form-error">{apiErrorMessage(accounts.error, 'No se pudo comprobar la conexión.')}</p>}{connected ? <button className="secondary-button danger-button" onClick={() => { if (window.confirm('¿Desconectar Google? Jarvis dejará de acceder a Gmail y Calendar.')) disconnect.mutate() }} disabled={disconnect.isPending}>{disconnect.isPending ? 'Desconectando…' : 'Desconectar Google'}</button> : <button className="primary-button" onClick={() => connect.mutate()} disabled={connect.isPending}>{connect.isPending ? 'Abriendo Google…' : 'Conectar Google'}</button>}</div></section>
}

function SpaceBackdrop() {
  return (
    <>
      <div className="empty-sky welcome-sky" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div>
      <div className="welcome-atlas" aria-hidden="true"><span /><span /><span /></div>
      <div className="welcome-constellations" aria-hidden="true">
        <svg viewBox="0 0 220 140"><path d="M8 110 29 91 42 72 58 78 72 93 87 66 106 45 123 52 138 61 151 39 164 17 181 31 211 48 193 72 181 101 158 88 138 61 121 82 106 45" /><circle cx="8" cy="110" r="2.2" /><circle cx="29" cy="91" r="1.4" /><circle cx="42" cy="72" r="2.2" /><circle cx="58" cy="78" r="1.4" /><circle cx="72" cy="93" r="2.2" /><circle cx="87" cy="66" r="1.4" /><circle cx="106" cy="45" r="2.2" /><circle cx="123" cy="52" r="1.4" /><circle cx="138" cy="61" r="2.2" /><circle cx="151" cy="39" r="1.4" /><circle cx="164" cy="17" r="2.2" /><circle cx="181" cy="31" r="1.4" /><circle cx="211" cy="48" r="2.2" /><circle cx="193" cy="72" r="1.4" /><circle cx="181" cy="101" r="2.2" /><circle cx="158" cy="88" r="1.4" /></svg>
        <svg viewBox="0 0 190 135"><path d="M11 27 27 52 43 77 58 60 72 49 85 72 101 97 115 76 129 56 143 84 159 111 170 74 181 44 151 38 129 56 101 97 72 49 43 77" /><circle cx="11" cy="27" r="2.2" /><circle cx="27" cy="52" r="1.4" /><circle cx="43" cy="77" r="2.2" /><circle cx="58" cy="60" r="1.4" /><circle cx="72" cy="49" r="2.2" /><circle cx="85" cy="72" r="1.4" /><circle cx="101" cy="97" r="2.2" /><circle cx="115" cy="76" r="1.4" /><circle cx="129" cy="56" r="2.2" /><circle cx="143" cy="84" r="1.4" /><circle cx="159" cy="111" r="2.2" /><circle cx="170" cy="74" r="1.4" /><circle cx="181" cy="44" r="2.2" /><circle cx="151" cy="38" r="1.4" /></svg>
        <svg viewBox="0 0 150 110"><path d="M9 80 22 52 36 25 49 40 65 55 78 36 91 20 104 46 118 72 131 57 143 42 126 84 118 72 87 94 65 55 36 25" /><circle cx="9" cy="80" r="2.2" /><circle cx="22" cy="52" r="1.4" /><circle cx="36" cy="25" r="2.2" /><circle cx="49" cy="40" r="1.4" /><circle cx="65" cy="55" r="2.2" /><circle cx="78" cy="36" r="1.4" /><circle cx="91" cy="20" r="2.2" /><circle cx="104" cy="46" r="1.4" /><circle cx="118" cy="72" r="2.2" /><circle cx="131" cy="57" r="1.4" /><circle cx="143" cy="42" r="2.2" /><circle cx="126" cy="84" r="1.4" /><circle cx="87" cy="94" r="2.2" /></svg>
      </div>
      <div className="welcome-systems" aria-hidden="true"><div className="planetary-system system-a"><b /><i /><i /><i /></div><div className="planetary-system system-b"><b /><i /><i /></div><div className="planetary-system system-c"><b /><i /><i /></div></div>
      <div className="welcome-rockets" aria-hidden="true"><span><i /><b /></span><span><i /><b /></span><span><i /><b /></span><span><i /><b /></span><span><i /><b /></span></div>
      <div className="empty-orbit" aria-hidden="true"><span /><span /><span /></div>
    </>
  )
}

function PageLoader({ label }: { label: string }) { return <div className="state-page"><span className="loader" />{label}</div> }
function PageError({ message, onRetry }: { message: string; onRetry: () => void }) { return <div className="state-page"><p>{message}</p><button className="secondary-button" onClick={onRetry}>Reintentar</button></div> }
function EmptyState({ title, description }: { title: string; description: string }) { return <div className="empty-state"><h2>{title}</h2><p>{description}</p></div> }
function NoConversations({ onCreate, creating }: { onCreate: () => void; creating: boolean }) { return <section className="no-conversations conversation-welcome"><SpaceBackdrop /><p className="eyebrow">Un espacio nuevo</p><h1>Empieza una conversación.</h1><p>Pregunta algo, organiza una idea o pídele a Jarvis que revise tu correo o calendario. El primer paso cabe en una frase.</p><button className="primary-button" onClick={onCreate} disabled={creating}>{creating ? 'Creando conversación…' : 'Crear mi primera conversación'}</button></section> }
function ConversationWelcome({ onCreate, creating }: { onCreate: () => void; creating: boolean }) { return <section className="no-conversations conversation-welcome"><div className="empty-sky welcome-sky" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div><div className="welcome-atlas" aria-hidden="true"><span /><span /><span /></div><div className="welcome-constellations" aria-hidden="true"><svg viewBox="0 0 220 140"><path d="M8 110 29 91 42 72 58 78 72 93 87 66 106 45 123 52 138 61 151 39 164 17 181 31 211 48 193 72 181 101 158 88 138 61 121 82 106 45" /><circle cx="8" cy="110" r="2.2" /><circle cx="29" cy="91" r="1.4" /><circle cx="42" cy="72" r="2.2" /><circle cx="58" cy="78" r="1.4" /><circle cx="72" cy="93" r="2.2" /><circle cx="87" cy="66" r="1.4" /><circle cx="106" cy="45" r="2.2" /><circle cx="123" cy="52" r="1.4" /><circle cx="138" cy="61" r="2.2" /><circle cx="151" cy="39" r="1.4" /><circle cx="164" cy="17" r="2.2" /><circle cx="181" cy="31" r="1.4" /><circle cx="211" cy="48" r="2.2" /><circle cx="193" cy="72" r="1.4" /><circle cx="181" cy="101" r="2.2" /><circle cx="158" cy="88" r="1.4" /></svg><svg viewBox="0 0 190 135"><path d="M11 27 27 52 43 77 58 60 72 49 85 72 101 97 115 76 129 56 143 84 159 111 170 74 181 44 151 38 129 56 101 97 72 49 43 77" /><circle cx="11" cy="27" r="2.2" /><circle cx="27" cy="52" r="1.4" /><circle cx="43" cy="77" r="2.2" /><circle cx="58" cy="60" r="1.4" /><circle cx="72" cy="49" r="2.2" /><circle cx="85" cy="72" r="1.4" /><circle cx="101" cy="97" r="2.2" /><circle cx="115" cy="76" r="1.4" /><circle cx="129" cy="56" r="2.2" /><circle cx="143" cy="84" r="1.4" /><circle cx="159" cy="111" r="2.2" /><circle cx="170" cy="74" r="1.4" /><circle cx="181" cy="44" r="2.2" /><circle cx="151" cy="38" r="1.4" /></svg><svg viewBox="0 0 150 110"><path d="M9 80 22 52 36 25 49 40 65 55 78 36 91 20 104 46 118 72 131 57 143 42 126 84 118 72 87 94 65 55 36 25" /><circle cx="9" cy="80" r="2.2" /><circle cx="22" cy="52" r="1.4" /><circle cx="36" cy="25" r="2.2" /><circle cx="49" cy="40" r="1.4" /><circle cx="65" cy="55" r="2.2" /><circle cx="78" cy="36" r="1.4" /><circle cx="91" cy="20" r="2.2" /><circle cx="104" cy="46" r="1.4" /><circle cx="118" cy="72" r="2.2" /><circle cx="131" cy="57" r="1.4" /><circle cx="143" cy="42" r="2.2" /><circle cx="126" cy="84" r="1.4" /><circle cx="87" cy="94" r="2.2" /></svg></div><div className="welcome-systems" aria-hidden="true"><div className="planetary-system system-a"><b /><i /><i /><i /></div><div className="planetary-system system-b"><b /><i /><i /></div><div className="planetary-system system-c"><b /><i /><i /></div></div><div className="welcome-rockets" aria-hidden="true"><span><i /><b /></span><span><i /><b /></span><span><i /><b /></span><span><i /><b /></span><span><i /><b /></span></div><div className="empty-orbit" aria-hidden="true"><span /><span /><span /></div><p className="eyebrow welcome-enter">Tu espacio de trabajo</p><h1 className="welcome-title"><span>Chatea ahora.</span></h1><p className="welcome-copy">Elige una conversación del panel lateral para continuar o abre una nueva para empezar algo distinto.</p><button className="primary-button welcome-action" onClick={onCreate} disabled={creating}>{creating ? 'Creando conversación…' : 'Nueva conversación'}</button></section> }
