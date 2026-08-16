# Phase 7.5 - Backend Stabilization and Tool Refactor

## Purpose

Phase 7 delivered a functional Gmail integration. Phase 7.5 turns that functionality into a reliable backend foundation before a production client is introduced. This phase does not add a new external integration or user-facing feature. It makes the existing auth, chat, OAuth, Gmail, tool, and temporary-state flows safe, testable, and maintainable.

Client implementation moves to a later phase. Building it now would couple a new interface to APIs and Gmail flows that are still being redesigned.

## Implementation status

Implemented during this phase:

- JWT access-token claims and expiration checks, CORS configuration, a shared API error shape, and safe provider timeouts.
- Alembic baseline migrations plus the `conversation_tool_state` lifecycle: one active state per user and conversation, typed state lookup, atomic replacement, and expiry.
- A synchronous Gmail client split by received mail, sent mail, drafts, search helpers, and request/error handling.
- Pydantic input and result schemas for Gmail tools. The implemented result contract uses `success`, optional `reason` and `message`, and typed email or draft fields; it does not use the earlier proposed `status` / `action` / `items` format.
- Gmail tools split into focused modules, with stateful selection flows protected by `state_type`.
- A declarative registry that stores each tool handler, schemas, and whether it requires `conversation_id`; the execution service validates both arguments and results.
- Intent routing split into prompt, parser, service, and tool-catalog responsibilities.
- Chat orchestration that keeps the current user message in memory until Gemini completes, then persists the user and assistant messages together in the normal success path.
- Tool results marked as untrusted external data before they are passed to the final Gemini response.
- Regression tests for Gmail flows, tool state, registry execution, intent parsing, chat orchestration, provider errors, and service error contracts.

Intentional exception:

- Debug `print()` statements remain temporarily for teaching demonstrations. They must not include tokens, passwords, complete email or draft bodies, complete prompts, or raw LLM responses. Structured logging remains a future cleanup item before production readiness.

## Scope

### 1. Preserve and verify the current Gmail milestone

- Review every current uncommitted Gmail change and manually verify the supported flows.
- Fix confirmed functional regressions before moving code.
- Create a clean Git checkpoint only after the existing behavior is understood and verified.
- Never discard working Gmail behavior merely to make the refactor easier.

### 2. Auth, configuration, and HTTP error foundation

- Include `sub`, `exp`, `iat`, and `type` in access JWTs and validate them consistently.
- Correct the OAuth2 documentation token URL.
- Add CORS configuration by environment before the browser client is introduced.
- Define an application error contract with stable error codes, user-safe messages, and optional details.
- Add global FastAPI exception handlers for validation, authentication, domain, Gemini, Google OAuth, and Gmail provider errors.
- Define provider request timeouts in configuration and apply them to every Google request.

Target API error shape:

```json
{
  "error": {
    "code": "external_provider_unavailable",
    "message": "Google Gmail is temporarily unavailable.",
    "details": {}
  }
}
```

### 3. Safe logging

- Replace every `print()` in request paths with structured logging.
- Log request ID, tool name, duration, result status, and safe internal identifiers.
- Never log access tokens, refresh tokens, full email bodies, draft bodies, complete prompts, or raw LLM responses in normal logs.

### 4. Database migrations and temporary tool state

Introduce Alembic before changing more database models. `Base.metadata.create_all()` is insufficient once a schema has real user data.

Refactor `conversation_tool_state` into one explicit pending state per conversation:

```text
conversation_id       unique active state owner
user_id               authorization check
state_type            expected follow-up flow
payload_json          candidates and pending arguments
expires_at            state lifetime
created_at
updated_at
```

Create one repository/service interface:

```text
save_tool_state(...)
load_tool_state(...)
clear_tool_state(...)
expire_tool_states(...)
```

Rules:

- A conversation has zero or one active pending state.
- A tool must validate `state_type` before using a selection.
- A successful, cancelled, or expired flow clears its state.
- Replacing a state is atomic.

### 5. Gmail integration client

Keep synchronous endpoints during this phase to avoid an unnecessary async rewrite. Centralize the synchronous HTTP behavior instead.

```text
app/integrations/gmail/
├── client.py          request session, timeout, Google error mapping
├── messages.py        received email API operations
├── drafts.py          draft API operations
├── sent.py            sent email API operations
└── search.py          query and date helpers
```

- Add timeouts and consistent handling for Google 401, 403, 404, 429, and 5xx responses.
- Fix the recent-email reader so it preserves message IDs until full content is retrieved.
- Centralize MIME decoding, metadata extraction, date normalization, and pagination helpers.
- Remove dead code only after tests cover the replacement path.

### 6. Typed Gmail tools

Replace free `arguments: dict` input with Pydantic schemas for every Gmail action.

```text
SearchReceivedEmailsArgs
ReadSpecificEmailArgs
CreateDraftArgs
UpdateDraftArgs
SendDraftArgs
MoveEmailToTrashArgs
DeleteDraftArgs
```

Schemas own validation for limits, date ranges, candidate positions, selection modes, and required action fields. Tools should not repeat manual `int()` conversions or validation branches.

### 7. Gmail tool module refactor

Replace the monolithic `app/tools/external/gmail_tools.py` with:

```text
app/tools/gmail/
├── inbox.py
├── sent.py
├── drafts.py
├── replies.py
├── selection.py
├── schemas.py
├── results.py
└── common.py
```

Product flow shared by every ambiguous Gmail action:

```text
search
├── no candidates      -> not_found
├── one candidate      -> execute action
└── many candidates    -> save state and request a numbered selection
```

Mutable actions always identify exactly one resource before executing. Sending, deleting, updating, and moving to Trash must never silently act on multiple items.

### 8. Tool registry and tool results

Replace the function-comparison dispatcher with declarative tool definitions:

```text
name
input_schema
handler
mutability
state_policy
```

Normalize tool outcomes:

```text
status: success | needs_selection | not_found | validation_error | provider_error
action: search | read | create | update | send | trash | delete
items: []
has_more: bool
message: str | null
```

### 9. Intent router and chat orchestration

- Split the intent router into prompt, parser, service, and tool catalog responsibilities.
- Remove duplicated Gmail rules and invalid JSON examples.
- Validate LLM output against the selected tool schema before execution.
- Use the registry as the tool catalog source of truth.
- Mark Gmail content passed to the final response model as external, untrusted data; it must not override system instructions.
- Update chat orchestration to use normalized results and preserve messages only when the flow is valid.

### 10. Tests and local quality gates

Add local test infrastructure and test the behavior before and after refactoring:

```text
tests/
├── core/
├── repositories/
├── routers/
├── services/
└── tools/gmail/
```

Required coverage:

- JWT issuance and expiration.
- Conversation ownership.
- OAuth state and token refresh.
- Tool-state save, replacement, expiration, and type validation.
- Chat with Gemini mocked.
- Recent-email reading.
- Search -> selection -> read.
- Search -> selection -> Trash.
- Search -> selection -> update, send, and delete draft.
- Gmail provider failures.

Add `pytest` and `ruff`, document their commands, and make a passing local suite a requirement for every refactor step. Remote CI belongs to Phase 9.

### 11. Documentation

- Update README to reflect Gemini, OAuth, and Gmail capabilities.
- Add `.env.example` without secrets.
- Document local Gmail/OAuth setup.
- Document the temporary-state design and destructive-action safety policy.
- Keep `CONTEXT.md` as roadmap and link to this file for Phase 7.5 detail.

## Execution order

1. Verify and checkpoint current Gmail behavior.
2. Add characterization tests for existing critical flows.
3. Fix JWT, CORS, error contract, logging, and provider timeouts.
4. Add Alembic and migrate temporary tool state.
5. Stabilize the Gmail integration client and fix confirmed bugs.
6. Create input/output schemas and shared tool helpers.
7. Split and refactor inbox, sent, drafts, replies, and selection tools.
8. Replace the registry/dispatcher and normalize tool results.
9. Modularize intent routing and adapt chat orchestration.
10. Complete regression tests, remove obsolete code, and update documentation.

Do not start a later step until the previous step is understood, manually verified when relevant, and covered by appropriate tests.

## Out of scope

- Client UI and OAuth callback UX.
- Google Calendar.
- Persistent memory.
- Voice pipeline.
- Docker image, full Compose, remote CI, deployment, and monitoring.
- Spotify and Notion.

Those items belong to Phases 8 through 12 under the revised roadmap in `CONTEXT.md`.

## Exit criteria

- Access JWTs expire correctly.
- CORS is configuration-driven and ready for browser client origins.
- Gmail and Gemini failures return stable, safe API errors.
- No sensitive request data is printed to normal logs.
- Every Gmail tool validates typed input and returns a normalized result.
- Pending selection state is typed, unique per conversation, and expires.
- Core Gmail flows pass automated tests with provider calls mocked.
- README, environment example, and architecture documentation reflect the implementation.
