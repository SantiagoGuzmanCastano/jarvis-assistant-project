# Phase 9 — Google Calendar MVP

Status: completed.

## Goal

Add safe Google Calendar actions to the existing conversational product without creating a separate calendar UI. The active client remains `web_app/`; Calendar is accessed through chat and the existing Google OAuth connection.

## Architecture

Calendar follows the backend layers already used by Gmail:

```text
intent router
-> typed tool registry
-> Calendar tool
-> service-level calculation or orchestration
-> Google Calendar integration client
```

- `schemas/tools/calendar.py` validates tool arguments.
- `schemas/tools/calendar_results.py` validates tool results.
- `tools/external/calendar/` owns tool flows and temporary selection/confirmation state.
- `services/calendar_availability.py` calculates free intervals from provider busy periods.
- `services/calendar_event_extraction.py` extracts an event proposal from selected Gmail content.
- `integrations/calendar/` owns Google Calendar HTTP requests and provider-response parsing.
- repositories only persist and retrieve state; they do not make product decisions.

## Public tools

### Read-only

- `calendar_get_upcoming_events` reads events in an explicit range. Missing bounds are resolved by the tool's documented defaults.
- `calendar_find_free_slots` requests Google free/busy periods and calculates intervals that can contain `duration_minutes`.

These tools never mutate Calendar.

### Preparation and creation

- `calendar_prepare_event_from_email` resolves exactly one received email, sent email, or draft using an active source, a recent position, a new search, or a previous candidate selection.
- Gemini extracts title, description, start/end, and location from that exact source. Explicit `event_*` arguments from the user override extracted values.
- Incomplete proposals are stored and returned with the missing fields.
- Complete proposals are stored and returned for confirmation.
- `calendar_create_event` with `confirmed: true` creates only the pending proposal.

Preparation does not create a Calendar event.

### Update

- `calendar_update_event` first searches for candidate events using the supplied title, description, or date range.
- Multiple matches require an exact `selected_result_position`.
- The tool fetches the selected event and prepares only the supplied `new_*` fields.
- `calendar_update_event` with `confirmed: true` applies the pending PATCH-like update.

Fields omitted from the update remain unchanged.

### Delete

- `calendar_delete_event` locates one exact non-recurring event.
- Multiple matches require an exact `selected_result_position`.
- The selected event is stored and presented before deletion.
- `calendar_delete_event` with `confirmed: true` deletes only that pending event.

## Temporary state

Calendar uses the existing `ConversationToolState` table. There is one replaceable, short-lived state per user and conversation; no Calendar-specific database table is required.

Relevant state types:

- `calendar_gmail_source_selection`
- `calendar_pending_event_creation`
- `calendar_event_update_selection`
- `calendar_pending_event_update`
- `calendar_event_delete_selection`
- `calendar_pending_event_delete`

Candidate positions shown to the user are one-based. Stored arrays remain zero-based internally, so selection flows validate the requested position before indexing.

## Timezones

Tool schemas accept IANA timezone names and default to `America/Bogota`. Naive datetimes are interpreted in the supplied timezone; aware datetimes are converted to it. End time must be later than start time.

Free/busy provider timestamps are parsed as timezone-aware datetimes before availability is calculated.

## OAuth

The shared Google connection requests existing Gmail scopes plus:

```text
https://www.googleapis.com/auth/calendar.events
https://www.googleapis.com/auth/calendar.events.freebusy
```

Users connected before these scopes were introduced must reconnect their Google account. Access tokens are refreshed through the existing OAuth token service.

## Safety rules

- Read and prepare tools never mutate Calendar.
- Create, update, and delete require a separate explicit confirmation.
- Gmail content must be selected and read exactly before event extraction.
- Ambiguous Gmail sources or Calendar events require user selection.
- External Gmail and Calendar content is untrusted when passed to Gemini.

## Out of scope

- recurring events
- reminders
- background synchronization
- automatic inbox scanning
- a dedicated calendar UI
- automatic invitation sending
- deleting recurring or multiple events
- preparing an event update from an email

## Verification

Automated tests mock Google and Gemini calls. Phase closure requires:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
Set-Location web_app
npm run lint
npm run build
```

Manual verification uses a real connected Google account and covers reading events, finding availability, preparing and confirming creation, PATCH-like update, deletion confirmation, OAuth reconnection, and token refresh.

## Technical closure

- Backend: `298 passed`.
- Database: one applied Alembic head, `050291b7b35a`, with no pending model operations.
- Frontend: lint and production build pass.
- Real Google account: Calendar reads, availability, confirmed creation/update/delete, Gmail-based preparation, OAuth reconnection, and token refresh verified.
