# Phase 8 — Flutter MVP Design

## Purpose

This document fixes the product navigation, screen ownership, and UI states
before Flutter code is created. The application targets Android, iOS, and Web;
initial development runs in Chrome against the local FastAPI backend.

## Product structure

```text
Authentication
├── Login
└── Registration

Application shell
├── Conversation drawer
│   ├── Create conversation
│   ├── Conversation list
│   └── Settings entry point
└── Main content
    ├── Selected conversation chat
    ├── Settings
    └── Google connection management
```

On Web, the conversation drawer is a persistent left sidebar. On mobile, the
same content is a slide-out drawer. This keeps conversations immediately
available without turning settings or Google connection into primary navigation
destinations.

## Startup and navigation

```text
App opens
-> local access token exists?
   -> no: Login
   -> yes: validate session
       -> invalid: Login
       -> valid, settings missing: Onboarding
       -> valid, settings present: Application shell
```

The application shell starts on the conversation list. Selecting a conversation
loads its chat in the main area. Creating a conversation selects it immediately.

## Screen ownership

| Screen | Backend contract | Product responsibility |
|---|---|---|
| Login | `POST /auth/login` | Starts a renewable application session. |
| Registration | `POST /auth/register` | Creates the account, then sends the user to login. |
| Onboarding | `POST /user_settings` | Creates first-time Jarvis settings. |
| Conversation drawer | `GET/POST /conversations` | Lists and creates conversations. |
| Chat | `GET /conversations/{id}`, `POST /chat/` | Loads history and talks with Jarvis. |
| Settings | `GET/PATCH /user_settings/me`, `PATCH /user_settings/reset` | Edits Jarvis identity and language preferences. |
| Google connection | `GET /external-auth/accounts`, `GET /external-auth/google/connect`, `DELETE /external-auth/google` | Connects or disconnects Google. |
| Logout | `POST /auth/logout` | Revokes the current refresh session and clears local tokens. |

## Required UI states

| Area | States |
|---|---|
| App bootstrap | Checking session, authenticated, expired, reauthentication required. |
| Login and registration | Idle, submitting, field validation error, credential error, provider/server error. |
| Conversation drawer | Loading, empty, populated, creating, creation error with retry. |
| Chat | No selection, loading history, empty conversation, ready, sending, assistant pending, error with controlled retry. |
| Settings | Loading, editing, saving, saved, error, reset confirmation. |
| Google connection | Disconnected, opening Google, awaiting callback, connected, reconnect required, disconnect confirmation, error. |
| Logout | Requesting logout, clearing local session, returned to login. |

Backend `404` responses have product meanings that must not become generic error
screens:

- `GET /user_settings/me` with `user_settings_not_found` opens onboarding.
- `GET /external-auth/accounts` with `external_accounts_not_found` means Google
  is disconnected.
- `GET /conversations` returning `[]` is an empty state.

## Renewable session behavior

Every protected request sends the current access token. When a request receives
`401`, the Flutter HTTP client refreshes the session once, replaces the stored
token pair, and retries the original request once. If refresh fails, it clears
the local session and routes to Login. The complete backend contract is in
[auth-session-refresh.md](auth-session-refresh.md).

## Google OAuth

The current backend callback returns JSON. The Flutter callback route cannot be
implemented until the frontend has a fixed Web origin and a mobile deep-link
strategy. The UI reserves `opening Google` and `awaiting callback` states now;
the backend redirect contract is implemented after the Flutter shell exists.

## Gmail safety

The chat UI must reserve explicit selection and confirmation states for Gmail
actions. Sending a draft, permanently deleting a draft, moving mail to Trash,
disconnecting Google, deleting a conversation, and resetting settings require a
visual confirmation.

The current chat response contains text only. Before the Gmail UI can render
reliable selection and confirmation controls, the backend must expose typed
interaction metadata instead of requiring Flutter to infer intent from natural
language.

## Visual direction

- Dark surfaces, high contrast, and one restrained accent color.
- Conversational clarity inspired by ChatGPT and Gemini without copying either
  interface.
- Minimal chrome: the drawer, message list, composer, and essential actions
  take priority over decoration.

## Implementation order

1. Create the Flutter shell, navigation, theme, and centralized HTTP client.
2. Implement login, registration, renewable session handling, and onboarding.
3. Implement the conversation drawer and chat shell.
4. Implement settings and the Google connection screen.
5. Add the Flutter OAuth return route, then adapt the backend callback.
6. Add typed Gmail interaction contracts and their confirmation/selection UI.
7. Verify all flows in Chrome before mobile adaptation.

## Technical implementation plan

The client will live in `flutter_app/`, separate from the FastAPI application.
That boundary mirrors the backend: widgets do not make HTTP calls directly;
feature controllers coordinate UI state, repositories own endpoint calls, and a
single API client owns authentication, errors, and retries.

```text
lib/
  app/                 # Bootstrap, router, theme
  core/
    config/            # API base URL from --dart-define
    network/           # Dio client, error mapping, auth interceptor
    session/           # Token store and session coordinator
    ui/                # Shared loading, error, empty, confirmation widgets
  features/
    auth/              # Login, registration, session bootstrap
    settings/          # Onboarding and settings
    conversations/     # Drawer, list, creation, deletion
    chat/              # History, message composer, chat state
    google_account/    # Connection state and disconnect
```

`flutter_riverpod` will expose immutable asynchronous UI state and dependency
injection. `dio` will be the only HTTP transport; its interceptor attaches the
access token, handles exactly one `401 -> refresh -> retry`, and converts the
backend error envelope into a typed application error. `flutter_secure_storage`
will store the token pair on Android and iOS. On Web, the first MVP keeps the
pair in memory: it is lost when the browser tab reloads, which is safer than
silently persisting bearer tokens in browser storage. A later backend change to
HttpOnly cookies would be required for durable web sessions with stronger XSS
protection.

The API base URL is never hard-coded. Chrome starts with
`--dart-define=API_BASE_URL=http://localhost:8000`; Android emulator and iOS
simulator values will be configured separately when those targets are tested.

### Endpoint coverage

| Endpoint | Flutter owner | Client behavior |
|---|---|---|
| `GET /health` | Bootstrap diagnostics | Development-only backend availability check; no user screen. |
| `POST /auth/register` | Registration | Validate email/password locally, submit, then route to Login. |
| `POST /auth/login` | Login | Store token pair, fetch current user, then resolve settings gate. |
| `GET /auth/me` | Session bootstrap | Verifies an existing application session. |
| `POST /auth/refresh` | Central session coordinator | Internal-only call after one protected request returns `401`. |
| `POST /auth/logout` | Settings/logout action | Revoke refresh session best-effort, clear tokens locally even on failure. |
| `POST /user_settings` | Onboarding | Creates the first user settings record. |
| `GET /user_settings/me` | Startup/settings | A settings-not-found error routes to onboarding. |
| `PATCH /user_settings` | Settings form | Saves only changed values. |
| `PATCH /user_settings/reset` | Settings form | Requires visual confirmation before resetting. |
| `GET /conversations` | Conversation drawer | Loading, empty, populated, error/retry states. |
| `POST /conversations` | New conversation action | Creates and immediately selects the returned conversation. |
| `GET /conversations/{id}` | Chat | Loads selected history, with a no-selection and retry state. |
| `DELETE /conversations/{id}` | Conversation drawer | Requires visual confirmation, then selects a safe remaining state. |
| `POST /conversations/{id}/messages` | No primary MVP screen | Kept in the repository as a low-level backend contract; the normal composer uses `/chat/` so Gemini, persistence, and tools stay in one flow. |
| `POST /chat/` | Chat composer | Adds optimistic user text only while sending; then appends the returned assistant text or shows retry. |
| `GET /external-auth/accounts` | Google connection | Empty/not-found means disconnected, not a generic error. |
| `GET /external-auth/google/connect` | Google connection | Obtains `auth_url` and opens the provider flow. |
| `GET /external-auth/google/callback` | OAuth return adapter | Backend work deferred until web origin and mobile deep-link return contract exist. |
| `DELETE /external-auth/google` | Google connection | Requires visual confirmation before disconnecting. |

All protected endpoint failures use the existing error envelope
`error.code`, `error.message`, and optional `error.details`. Form validation
errors remain close to their fields; endpoint and connectivity errors use an
inline retry state, never an uninformative blank screen.

### Delivery sequence

1. Verify Flutter SDK and Chrome tooling, create the empty project, and add
   only the dependencies above.
2. Build the app bootstrap, token store, HTTP client, error model, route guard,
   and shared states. This establishes the contract every later feature uses.
3. Deliver Login, Registration, renewable session handling, Logout, and the
   settings onboarding gate.
4. Deliver the responsive application shell, conversation drawer, creation,
   deletion confirmation, history, and text chat.
5. Deliver settings editing and Google account status/disconnection. Connection
   initiation is included; callback completion follows the return-contract
   change.
6. Add the typed Gmail interaction contract in the backend, then its Flutter
   selection and confirmation controls. Text parsing is not an acceptable
   substitute for that contract.
7. Run Dart unit/widget tests and Chrome manual flows. Only then iterate on
   the dark cyberpunk visual system.
