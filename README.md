# Jarvis Assistant

Jarvis is an AI-powered personal assistant backend built as a learning-focused project for backend architecture, applied AI, and real-world integrations.

The current backend supports authentication, conversations, Gemini-powered chat, assistant personality settings, and a first internal tool execution flow.

## Current Status

Completed:

- Phase 1: Backend structure and authentication
- Phase 2: Conversations and messages
- Phase 3: Gemini text chat with conversation history
- Phase 4: Jarvis personality and user settings
- Phase 5: Tool system base

Pending:

- External OAuth and token storage
- Gmail, Calendar, Spotify, and Notion tools
- Persistent memory
- Tests, Docker polish, and documentation cleanup
- Flutter app
- Voice pipeline
- Proactivity and deployment

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- JWT authentication
- Gemini API
- Bruno for manual API testing

## Architecture

The backend is organized by responsibility:

```text
app/
├── core/            # configuration and security helpers
├── db/              # database session and initialization
├── dependencies/    # FastAPI dependencies
├── integrations/    # external API clients
├── models/          # SQLAlchemy models
├── repositories/    # database access
├── routers/         # HTTP endpoints
├── schemas/         # Pydantic schemas
├── services/        # business logic
└── tools/           # backend tools/actions
```

Main rule:

```text
routers receive HTTP requests
services coordinate business logic
repositories access the database
integrations talk to external APIs
tools execute backend actions
```

## Main Features

### Authentication

- User registration
- User login
- JWT access tokens
- Protected current-user endpoint

### Conversations

- Create conversations
- List current user's conversations
- Read one conversation with messages
- Add messages to a conversation
- Delete owned conversations

### Gemini Chat

The chat flow:

```text
POST /chat
→ validate conversation ownership
→ save user message
→ load user settings
→ build Jarvis system prompt
→ load conversation history
→ format messages for Gemini
→ generate assistant response
→ save assistant response
```

### User Settings

Each user can configure:

- assistant name
- assistant personality
- language mode

These settings are injected into the system prompt before each chat response.

### Tool System Base

Phase 5 adds the first backend tool architecture.

Current demo tool:

```text
get_current_time
```

Tool flow:

```text
user message
→ detect_tool_intent()
→ ToolIntent
→ tool_execution_system()
→ Tool Registry
→ backend tool function
→ tool_result
→ Gemini final response
```

Important rule:

```text
Gemini chooses intent.
The backend executes tools.
Tools are Python code.
```

Only the user message and final assistant response are saved as conversation messages. Tool context is temporary and only sent to Gemini for the final response.

## Main Endpoints

Auth:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

Conversations:

```text
POST   /conversations
GET    /conversations
GET    /conversations/{conversation_id}
POST   /conversations/{conversation_id}/messages
DELETE /conversations/{conversation_id}
```

Chat:

```text
POST /chat
```

User settings:

```text
POST  /user-settings
GET   /user-settings
PATCH /user-settings
```

## Backend Setup

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the FastAPI server:

```powershell
uvicorn app.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Environment Variables

The backend expects environment configuration for database access, JWT security, and Gemini.

Do not commit `.env`.

## Bruno

Bruno is used for manual API testing.

Use the local server URL:

```text
http://127.0.0.1:8000
```
