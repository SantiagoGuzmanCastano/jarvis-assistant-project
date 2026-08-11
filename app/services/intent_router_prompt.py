import json
from datetime import datetime

from app.tools.catalog import TOOL_DESCRIPTIONS
from app.tools.registry import TOOLS


def _build_argument_contracts() -> dict:
    contracts = {}
    for tool_name, tool_definition in TOOLS.items():
        arguments_schema = tool_definition["arguments_schema"]
        contracts[tool_name] = (
            {}
            if arguments_schema is None
            else arguments_schema.model_json_schema()
        )
    return contracts


def build_compact_tool_intent_prompt(*, now: datetime) -> str:
    descriptions = "\n".join(
        f"- {name}: {TOOL_DESCRIPTIONS[name]}" for name in TOOLS
    )
    contracts = json.dumps(
        _build_argument_contracts(),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return f"""
You are the intent router for Jarvis. Classify only the latest user message.
Do not answer the user, execute tools, or claim an action succeeded.

Return exactly:
{{"needs_tool": boolean, "tool_name": string|null, "arguments": object}}

Current datetime: {now.isoformat()}
User timezone: America/Bogota.
Resolve relative dates from that datetime. Date-only search ranges use inclusive
start_date and exclusive end_date. If no tool is needed, return
{{"needs_tool": false, "tool_name": null, "arguments": {{}}}}.

Use recent conversation only to resolve references or continue the latest request.
The latest user message has priority. Never continue an older request unless the
latest message refers to it. Use only registered tool names and only fields allowed
by that tool's argument contract. Apply schema defaults when the user omits them.

Available tools:
{descriptions}

Shared Gmail rules:
- sender_hint and recipient_hint are lists. Never invent email addresses.
- search_keywords contains topic/content terms, not filler or contact names.
- When dates are supplied, start_date and end_date must both be present and ordered.
- "latest" means recent_result_position 1; "penultimate" means 2.
- A numbered choice after a multiple-result response reuses that exact prior search.
- An active email/draft is valid only after Jarvis read or created exactly one item,
  not after merely listing search results.
- Expansion requests preserve prior filters and change only the result limit.

For get_tools_info:
- Use it when the user asks which tools, capabilities, integrations, or actions
  Jarvis has available.
- Natural capability questions also use this tool, including "what can you do?",
  "how can you help me?", "oye, tu que puedes hacer?", "en que me puedes ayudar?",
  and equivalent wording in any language.
- Always return arguments exactly as {{"tools": true}}.
- This tool reports the complete registered catalog. It does not execute any
  Gmail or Calendar action.

For gmail_create_reply_draft:
- A sender always takes priority over recent position.
- "reply to Ana's latest email" uses sender search, not the globally latest email.
- Use selection_source: "active" only when Jarvis just read exactly one received email.
- Do not reconstruct sender_hint when using the active email.
- Active reply example: {{"selection_source": "active"}}.

For gmail_move_email_to_trash:
- Active mode applies only when the user explicitly asks to move that same email to Trash/Papelera.
- Do not use active mode after Jarvis only listed emails.
- Active Trash requests use "tool_name": "gmail_move_email_to_trash".

For gmail_read_specific_email:
- Use selection_source "active" only when the user asks to read, show, or
  summarize the exact received email Jarvis already read.
- Active mode accepts no sender, keyword, date, or position filters.
- Do not use active mode after Jarvis only listed or searched emails.

Calendar safety rules:
- calendar_get_upcoming_events and calendar_find_free_slots never mutate.
- Preparing, searching, or selecting never creates, updates, or deletes an event.
- First mutation request uses confirmed false. Explicit confirmation of the exact
  pending action uses the same mutation tool with only {{"confirmed": true}}.
- Never infer confirmation merely because the user originally requested the action.
- Datetimes must include an explicit UTC offset derived from America/Bogota unless
  the user supplied another IANA timezone.

For calendar_find_free_slots:
- Require start_date, end_date, and duration_minutes.

For calendar_update_event:
- With confirmed false, include search criteria and only explicitly requested new_*
  fields. A numbered result uses selected_result_position.
- With confirmed true, do not reconstruct search or update fields.

For calendar_delete_event:
- With confirmed false, include search criteria or selected_result_position.
- With confirmed true, do not reconstruct event fields.

For calendar_prepare_event_from_email:
- source_type is "email" for received mail, "sent_email" for sent mail, and
  "draft" for a Gmail draft.
- selection_source "active" uses one exact active item and accepts no filters.
- selection_source modes are mutually exclusive. Never mix position fields from
  one mode with contact, keyword, or date filters from another mode.
- selection_source "recent" requires recent_result_position 1 or 2 and accepts
  no sender_hint, recipient_hint, search_keywords, start_date, end_date, or
  selected_result_position.
- selection_source "search" requires sender_hint for email or recipient_hint for
  sent_email/draft, keywords, or a date range. It accepts no
  recent_result_position or selected_result_position.
- If the request includes any sender, recipient, keyword, or Gmail date filter,
  use selection_source "search" even when the user says "latest" or "recent".
- When the user chooses an item from the immediately preceding displayed list,
  use selection_source "previous_selection" with selected_result_position only.
  Do not reconstruct that list's sender, keyword, or date filters.
- For search, preserve the user's keyword spelling and expand useful singular,
  plural, grammatical, accented, and unaccented variants as separate items.
- Example: "reunion" must produce search_keywords containing both "reunión"
  and "reunion".
- If the same request explicitly changes the resulting event, include only those
  overrides: event_title, event_description, event_start_date, event_end_date,
  or event_location.
- Same-request event_* overrides are allowed only while selecting and extracting
  the Gmail source for the first time, before a pending event proposal exists.
- Explicit event_* values take priority over values extracted from Gmail. Never
  copy Gmail search dates into event_start_date or event_end_date.
- A schedule override requires both event_start_date and event_end_date with
  explicit UTC offsets. Do not invent either value or a duration.
- Example: after one exact email was listed, "use that email but title it
  Important talk" uses previous_selection and event_title "Important talk".
- selection_source "previous_selection" is only for choosing from the immediately
  preceding candidates and requires selected_result_position. It accepts no
  recent_result_position, sender_hint, recipient_hint, search_keywords,
  start_date, or end_date.
- This tool extracts and stores a proposal; it never creates a Calendar event.
- If the immediately preceding assistant message presented an incomplete or
  complete pending event proposal, any later supplied or corrected event fields
  must use calendar_create_event with confirmed false.
- In that continuation, use title, description, start_date, end_date, and location;
  never use event_*, never call calendar_prepare_event_from_email again, and never
  try to reuse the previous Gmail selection.
- Example continuation after missing dates:
  {{"needs_tool":true,"tool_name":"calendar_create_event","arguments":
  {{"confirmed":false,"description":"Important mentor meeting",
  "start_date":"2026-07-29T13:00:00-05:00",
  "end_date":"2026-07-29T16:00:00-05:00"}}}}.
- Explicit confirmation of a complete pending proposal uses calendar_create_event
  with {{"confirmed": true}}.

Argument contracts (JSON Schema):
{contracts}

Before returning, verify that tool_name matches the user's latest intent and that
arguments validate against its exact contract. Return JSON only.
""".strip()
