# Jarvis — Project Context

## Description

Jarvis is an AI-powered personal assistant for iOS and Android built as an advanced learning project focused on backend engineering and applied AI.

The application allows users to interact through voice or text with an assistant capable of understanding natural language and executing real actions using external integrations such as Gmail, Google Calendar, Spotify, and Notion.

The main goal is NOT to build a full commercial product, but to deeply learn modern backend architecture, LLM integrations, real-world APIs, and AI system design.

---

## MVP Goal

Build a functional assistant capable of:

- receiving audio from a mobile app
- transcribing speech into text
- understanding user intent using an LLM
- executing real actions through APIs
- responding using both text and voice

---

## MVP Features

**Voice**
- audio recording from Flutter
- speech-to-text using Whisper API
- voice responses using ElevenLabs TTS
- fully bidirectional voice interaction

**AI**
- intent understanding
- natural language responses
- persistent memory between sessions
- basic tools/actions system
- proactive greeting on app open (emails pending, events of the day, reminders)

**Gmail**
- read unread emails
- summarize emails
- draft replies
- send emails after confirmation

**Google Calendar**
- read daily and tomorrow's schedule
- create events with natural language
- create simple reminders

**Spotify**
- play specific songs or artists
- play specific playlists
- requires Spotify Premium

**Notion (Notes)**
- create notes by dictating
- read existing notes
- search notes by title or content
- edit existing notes

---

## Jarvis Personality

Jarvis is not a neutral assistant. It has a defined personality that is consistent across all interactions.

**Character**
Loyal, helpful, and sharp — like Alfred from DC. A good friend, a reliable companion. Never a pushover. If the user makes a bad decision or says something wrong, Jarvis says so directly but respectfully. It does not flatter, does not over-encourage, and does not act complacent. It lifts the user's mood when appropriate, but naturally — the way a real friend would, not a motivational coach.

**Language and register**
Detects the user's language automatically and responds in the same language. Adapts to the user's register — formal if the user is formal, uses slang if the user uses slang. Never imposes a tone. Always respectful regardless of register.

**Opinions**
Has its own opinions and expresses them directly when asked. Defends them with arguments. If the user disagrees, accepts it without conflict and can debate calmly — never forces its view.

**Customizable name**
Each user can give Jarvis a custom name on first setup. That name is stored in the DB and used in the system prompt. One user calls it Jarvis, another calls it Alfred — same personality, different name.

**Proactivity**
When the user opens the app, Jarvis greets them and gives a brief summary of what is pending: unread emails, events of the day, active reminders. Does this automatically without being asked.

**Conversational**
When no tool is needed, Jarvis simply converses. It can talk about football, share a fun fact, or just chat. It is a work tool first, but it is not a robot.

---

## Tech Stack

**Backend**
- Python
- FastAPI
- Pydantic
- SQLAlchemy and SQLModel
- PostgreSQL
- JWT Authentication

**Frontend**
- Flutter

**AI & Voice**
- OpenAI API (ChatGPT + Whisper)
- ElevenLabs API (Text-to-Speech)

**Integrations**
- Gmail API
- Google Calendar API
- Spotify API
- Notion API
- Google OAuth 2.0

**Infrastructure**
- Docker
- Git
- GitHub

---

## Planned Architecture

**High-level flow:**
```
Flutter Frontend → FastAPI Backend → Voice Pipeline → Agent (ChatGPT) → Intent Router → Tool Execution Layer → External APIs
                                                            ↕
                                                       Memory (DB)
```

**Step by step:**
```
1. Flutter records audio and sends it to the backend
2. Backend sends audio to Whisper API → receives transcribed text
3. Backend sends text + conversation history + user memory to ChatGPT
4. ChatGPT reads the context and decides which tool to call (Intent Router)
5. Backend executes the chosen tool (Tool Execution Layer)
6. Tool calls the external API (Gmail, Calendar, Spotify, Notion)
7. ChatGPT generates a natural language response based on the result
8. Backend sends the response text to ElevenLabs → receives audio
9. Flutter receives the audio and plays it
```

**Memory is always involved in step 3:**
- conversation history → what was said in this session
- persistent memory → things the user has told Jarvis across all sessions

The backend is organized using layers:

```
app/
├── routers/          # endpoints exposed to Flutter (auth, voice, conversations)
├── services/         # business logic (agent, memory, voice pipeline)
├── repositories/     # database access (users, conversations, memory)
├── models/           # SQLAlchemy database models
├── schemas/          # Pydantic request/response schemas
└── integrations/     # external API clients
    ├── gmail.py
    ├── calendar.py
    ├── spotify.py
    ├── notion.py
    ├── whisper.py
    └── tts.py
```

**Key architectural rules:**
- Assistant logic must NOT be mixed directly with API endpoints
- Each integration lives in its own isolated module
- The intent router decides which tool to call — it does not execute the tool itself
- Services coordinate between the agent, memory, and integrations
- Repositories are the only layer that touches the database

---

## Project Philosophy

This project exists mainly for learning purposes.

Main priorities:

1. Understand before moving forward
2. Build important parts manually
3. Avoid unnecessary magic frameworks
4. Prioritize clean architecture
5. Learn debugging and real system design

The goal is NOT to vibe code or auto-generate the entire project.

---

## Documentation and Development Workflow

- All important architectural decisions should be documented
- Features should be documented as they are implemented
- The project should maintain a clean and professional README
- Changes should be committed frequently using meaningful commit messages
- Progress should be continuously pushed to GitHub
- The repository should reflect the real development process from start to finish
- Documentation should evolve together with the code

**Before every action** — creating a file, writing a function, adding a dependency — verify that what we are about to do is well placed within the project structure and makes sense at this point in the roadmap. Do not move forward if something is out of place.

---

## Current Status

**Completed**
- basic/intermediate FastAPI knowledge
- CRUD APIs
- JWT authentication
- basic testing
- basic database handling

**Pending**
- initial project architecture
- complete authentication system
- Flutter ↔ FastAPI integration
- voice pipeline (Whisper + ElevenLabs)
- Google OAuth 2.0
- Gmail integration
- Google Calendar integration
- Spotify integration
- Notion integration
- persistent memory

---

## Roadmap

### Phase 1 — Backend Structure + Auth
- project folder structure
- environment variables with `.env`
- database setup with SQLAlchemy
- user model
- JWT registration and login
- protected endpoints with dependencies

**Deliverable:** auth working in Postman (register, login, protected endpoint)

---

### Phase 2 — Flutter ↔ Backend + Voice Pipeline
- basic Flutter app structure
- login screen connected to backend
- audio recording from microphone
- audio upload to backend
- Whisper API integration (speech-to-text)
- ElevenLabs API integration (text-to-speech)
- Flutter plays audio response

**Deliverable:** speak into the app, receive an audio response from the backend

---

### Phase 3 — Intent Router + Tool System + Personality
- ChatGPT API integration
- system prompt design: Jarvis personality, language detection, opinion handling, conversational behavior
- customizable assistant name stored in DB and injected into system prompt
- function calling: ChatGPT decides which tool to use
- tool execution layer (each integration is a callable tool)
- conversation history in DB (session memory)

**Deliverable:** agent receives text, responds with personality, decides which tool to call when needed

---

### Phase 4 — Google OAuth + Gmail
- Google OAuth 2.0 flow
- Google Cloud Console setup (credentials, scopes)
- store and refresh Google tokens per user
- Gmail API: read, summarize, draft, send

**Deliverable:** ask the agent to read or send emails, it works end-to-end

---

### Phase 5 — Google Calendar
- Google Calendar API: list events, create events, create reminders
- connected to the tool system

**Deliverable:** ask the agent about your schedule or to create an event, it works

---

### Phase 6 — Spotify
- Spotify OAuth and API setup
- search songs, artists, playlists
- control playback (requires Spotify Premium)

**Deliverable:** ask the agent to play something, it plays on Spotify

---

### Phase 7 — Notion
- Notion API setup and authentication
- create pages/notes by dictating
- read and search existing notes
- edit existing notes

**Deliverable:** ask the agent to create or read a note, it works in Notion

---

### Phase 8 — Persistent Memory
- persistent memory table in DB
- agent saves and retrieves important user information automatically
- conversation summarization to avoid filling context window

**Deliverable:** agent remembers things said in previous sessions

---

### Phase 9 — Proactivity + Polish + Docker + Deployment
- proactive greeting on app open: unread emails, events of the day, active reminders
- edge cases and bug fixing
- smooth end-to-end voice flow
- visible error handling for the user
- Docker setup
- deployment
- full demo rehearsal

**Deliverable:** Jarvis working end-to-end, greets proactively, ready for demo

---

## What is NOT in the MVP (v2)

- WhatsApp (technically impossible with official APIs)
- Full device control
- Smart Spotify recommendations
- Multi-user support
- Image recognition

---

## Professional Goal

This project should become a strong portfolio piece for backend engineering focused on applied AI before the end of 2026.

---

## How We Work

At the start of each session paste this file and say which phase you are on and what you just finished. That way we start without losing context.

Before writing any line of code, explain what we are going to do and why. If something is not understood at 90%, ask before continuing.
