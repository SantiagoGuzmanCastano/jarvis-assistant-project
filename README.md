# Jarvis Assistant

Jarvis is a learning-focused FastAPI backend for a conversational assistant. It combines PostgreSQL, JWT authentication, Gemini, Google OAuth, and Gmail actions. Flutter is intentionally deferred to Phase 10 while the backend contracts are stabilized.

## Current status

Completed:

- Phases 1-6: backend foundation, authentication, conversations, Gemini chat, user settings, base tools, and Google OAuth token storage.
- Phase 7: Gmail listing, search, reading, drafts, reply drafts, sending, updates, deletion, and move-to-Trash flows.
- Phase 7.5: backend stabilization and tool refactor, including typed Gmail contracts, Alembic migrations, temporary tool state, normalized errors, and regression coverage.

Next priority:

- Phase 8: Persistent Memory.

Out of scope for this phase: Flutter, Calendar, persistent memory, voice, Docker/CI, and new integrations.

## Architecture

```text
routers        HTTP endpoints and dependencies
services       business and chat orchestration
repositories   PostgreSQL access
models         SQLAlchemy database tables
schemas        Pydantic validation and serialized contracts
integrations   Gemini, Google OAuth, and Gmail clients
tools          Gmail actions selected by the intent router
```

The tool flow is:

```text
user message
-> intent router (Gemini)
-> validated tool registry entry
-> tool execution
-> validated tool result
-> untrusted tool context for Gemini
-> final assistant response
```

Gemini chooses a tool; only backend Python code executes it. Gmail data is treated as external untrusted content when passed back to Gemini.

## Gmail behavior

- Search and list flows return small batches and can expand up to 15 results.
- An ambiguous action stores one typed, temporary selection state per user and conversation.
- State expires automatically and is replaced atomically when a new pending action begins.
- Mutable actions identify exactly one email or draft before sending, updating, moving to Trash, or deleting it.
- Gmail provider failures are mapped to stable application errors.

## Error contract

Application errors use this HTTP response shape:

```json
{
  "error": {
    "code": "external_provider_unavailable",
    "message": "Google Gmail is temporarily unavailable.",
    "details": {}
  }
}
```

Services and repositories raise `AppError` for business failures. FastAPI dependencies and global handlers remain the HTTP boundary.

## Local setup

Create a local `.env` from `.env.example`, then fill in real secrets. Never commit `.env`.

```powershell
Copy-Item .env.example .env
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the API documentation at `http://127.0.0.1:8000/docs`.

## Database migrations

Alembic tracks schema changes. After changing a SQLAlchemy model:

```powershell
.\.venv\Scripts\alembic.exe revision --autogenerate -m "describe schema change"
.\.venv\Scripts\alembic.exe upgrade head
```

Review every generated migration before running `upgrade head`.

## Tests

Run the complete suite without pytest cache writes:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Provider calls are mocked in tests. Use Bruno and a connected Google account only for manual Gmail smoke checks.
