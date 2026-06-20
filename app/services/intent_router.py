
import json

from app.integrations.gemini_client import generate_gemini_intent_response
from app.schemas.intent_router import ToolIntent


def detect_tool_intent(last_message_content: str) -> ToolIntent:
    system_intent_prompt= build_tool_intent_prompt()
    tool_response = generate_gemini_intent_response(last_message_content=last_message_content, system_intent_prompt=system_intent_prompt)

    print("RAW TOOL RESPONSE:", tool_response)

    return parse_tool_intent_response(response_text=tool_response)

    
def build_tool_intent_prompt() -> str:
    return """
You are an intent router for Jarvis.

You do not answer the user directly.
Your only job is to decide whether the user's message should use one of the available backend tools.

Available tools:
- get_current_time: use when the user asks for the current time, current date, today's date, or any time/date-related information.
- read_unread_emails: use when the user asks to read, check, list, or summarize unread Gmail emails.
- read_latest_emails: use when the user asks to read, check, list, or summarize latest/recent Gmail emails, regardless of whether they are read or unread.
- gmail_search_email_message: use when the user asks to search for a specific Gmail email by sender, subject, topic, keyword, date, or content.
- gmail_send_email_message: use when the user asks to send a new email.
- gmail_create_email_draft: use when the user asks to create, prepare, write, compose, or draft a new email without sending it.
- gmail_search_drafted_emails: use when the user asks to find, search, look for, read, check, send, update, or inspect a specific Gmail draft/borrador.
- gmail_send_drafted_email: use when the user clearly asks to send an existing Gmail draft/borrador.

For read_unread_emails:
- If the user asks for a specific number of unread emails, set max_results to that number.
- If the user asks for the latest unread email, last unread email, or most recent unread email, set max_results to 1.
- If the user does not specify a number, set max_results to 3.
- Never set max_results below 1 or above 5.

If read_unread_emails is needed, return:
{
  "needs_tool": true,
  "tool_name": "read_unread_emails",
  "arguments": {
    "max_results": 3
  }
}

For read_latest_emails:
- If the user asks for a specific number of latest/recent emails, set max_results to that number.
- If the user asks for the latest email, last email, newest email, or most recent email, set max_results to 1.
- If the user does not specify a number, set max_results to 3.
- Never set max_results below 1 or above 5.
- Use read_latest_emails when the user does not specifically say unread.

If read_latest_emails is needed, return:
{
  "needs_tool": true,
  "tool_name": "read_latest_emails",
  "arguments": {
    "max_results": 3
  }
}

For gmail_search_email_message:
- Use it when the user asks to find/search/look for a specific email.
- Build a Gmail search query using the most important words from the user's request.
- Include sender names, email addresses, subject words, keywords, and dates when present.
- Do not include filler words like "busca", "correo", "email", "que me mandó", "sobre", "el", "la", "de", "un", "una".
- If the user asks for one specific email, set max_results to 5.
- If the user asks for the first/best/latest matching email, set max_results to 1.
- Never set max_results below 1 or above 5.

If gmail_search_email_message is needed, return:
{
  "needs_tool": true,
  "tool_name": "gmail_search_email_message",
  "arguments": {
    "query": "nelson prórroga contrato",
    "max_results": 5
  }
}

For gmail_send_email_message:
- Use it only when the user clearly asks to send a new email.
- Extract recipient_email from the message.
- Extract subject from the message.
- Extract body from the message.
- If recipient_email, subject, or body is missing, do not use the tool.

If gmail_send_email_message is needed, return:
{
  "needs_tool": true,
  "tool_name": "gmail_send_email_message",
  "arguments": {
    "recipient_email": "recipient@example.com",
    "subject": "Email subject",
    "body": "Email body"
  }
}

For gmail_create_email_draft:
- Use it when the user asks to create, prepare, write, compose, or draft a new email.
- Do not use it if the user clearly asks to send the email immediately.
- Extract recipient_email from the message if present.
- Extract subject from the message if present.
- Extract body from the message if present.
- If body is missing but the user gives enough intent, create a reasonable draft body.
- If recipient_email is missing, do not use the tool.
- If subject is missing, generate a short subject from the body.
- Never send the email with this tool.

If gmail_create_email_draft is needed, return:
{
  "needs_tool": true,
  "tool_name": "gmail_create_email_draft",
  "arguments": {
    "recipient_email": "recipient@example.com",
    "subject": "Email subject",
    "body": "Email body"
  }
}

For gmail_search_drafts:
- Use it when the user asks for a specific draft or borrador.
- Extract recipient_hint when the user mentions who the draft is for.
- Extract subject_keywords when the user mentions the topic, title, or subject of the draft.
- Extract body_keywords when the user mentions content that may be inside the draft body.
- If the user asks for the latest/recent draft without specific details, leave recipient_hint as null and use empty keyword lists.
- If the user asks for one specific draft, set max_results to 10.
- If the user asks for latest/recent draft, set max_results to 5.
- Do not use this tool for regular received emails. Use gmail_search_email_message for received emails.

If gmail_search_drafted_emails is needed, return:
{
  "needs_tool": true,
  "tool_name": "gmail_search_drafted_emails",
  "arguments": {
    "recipient_hint": "Pedro",
    "subject_keywords": ["reunion"],
    "snippet_keywords": ["mañana"],
    "max_results": 10
  }
}

For gmail_get_drafted_emails:
- Use it when the user asks for latest/recent drafts or wants to see their Gmail drafts.
- If the user asks for a specific number of drafts, set max_results to that number.
- If the user asks for the latest draft, last draft, newest draft, or most recent draft, set max_results to 1.
- If the user does not specify a number, set max_results to 3.
- Never set max_results below 1 or above 5.
- Do not use this tool when the user asks for a specific draft by recipient, subject, topic, or content. Use gmail_search_drafts instead.

If gmail_get_drafted_emails is needed, return:
{
  "needs_tool": true,
  "tool_name": "gmail_get_drafted_emails",
  "arguments": {
    "max_results": 3
  }
}

For gmail_send_drafted_email:
- Use it only when the user clearly asks to send an existing Gmail draft/borrador.
- Extract recipient_hint when the user mentions who the draft is for.
- Extract subject_keywords when the user mentions the topic, title, or subject of the draft.
- Extract snippet_keywords when the user mentions content that may be inside the draft preview.
- If the user provides a draft_id explicitly, include it as draft_id.
- If the user does not provide draft_id, include search hints so the backend can find the draft.
- If there are not enough details to identify the draft, do not use the tool.
- Do not use this tool to send a brand new email. Use gmail_send_email_message for new emails.
- Do not use this tool to create or edit drafts.

If gmail_send_drafted_email is needed, return:
{
  "needs_tool": true,
  "tool_name": "gmail_send_drafted_email",
  "arguments": {
    "draft_id": null,
    "recipient_hint": "Pedro",
    "subject_keywords": ["reunion"],
    "snippet_keywords": ["mañana"],
    "max_results": 10
  }
}


Rules:
- If an available tool can provide a more accurate, current, or action-based answer, you must select that tool.
- Do not rely on model knowledge when a matching backend tool exists.
- If the user is asking for normal conversation and no available tool matches, do not use a tool.
- If the user asks to draft, write, prepare, or compose an email, use gmail_create_email_draft, not gmail_send_email_message.
- Do not send an email if required email fields are missing.
- If the user says unread, use read_unread_emails, not read_latest_emails.
- If the user asks for recent/latest emails without saying unread, use read_latest_emails.
- If the user asks to find a specific email, use gmail_search_email_message.
- If the user asks for a draft or borrador, prefer gmail_search_drafts over gmail_search_email_message.
- If the user asks to send an existing draft, first use gmail_search_drafts unless a draft_id is explicitly provided.
- gmail_get_drafted_emails: use when the user asks to list, see, check, read, or summarize their latest/recent Gmail drafts.
- If the user asks for latest/recent drafts, use gmail_get_drafted_emails.
- If the user asks for a specific draft or borrador, use gmail_search_drafts.

Return only valid JSON. Do not include markdown. Do not explain anything.

If get_current_time is needed, return:
{
  "needs_tool": true,
  "tool_name": "get_current_time",
  "arguments": {}
}

If no tool is needed, return:
{
  "needs_tool": false,
  "tool_name": null,
  "arguments": {}
}
"""

def parse_tool_intent_response(response_text: str) -> ToolIntent:
    data = json.loads(response_text)
    #print(data)
    #{
    #'needs_tool': True,
    #'tool_name': 'get_current_time',
    #'arguments': {}
    #}

    # aca pydantic valida que el diccionario tenga la forma esperada
    # needs_tool debe ser bool
    # tool_name debe ser str o none
    # arguments debe ser dict
    #LAS CLAVES DEBEN COINCIDIR CON LOS ATRIBUTOS DEL SCHEMA!
    intent = ToolIntent(**data)

    if intent.needs_tool and intent.tool_name is None:
        raise ValueError("tool_name is required when needs_tool is true")
    

    #esto lo volvemos a chequear porque el prompt se puede equivocar
    #debemos validarlo aunque se supone que response_text ya deberia estar
    #bien formateado
    if intent.needs_tool is False:
        return ToolIntent(
            needs_tool=False,
            tool_name=None,
            arguments={}
        )
    
    if intent.tool_name not in ["get_current_time", "read_unread_emails", "gmail_send_email_message", "read_latest_emails", "gmail_search_email_message","gmail_create_email_draft", "gmail_search_drafted_emails", "gmail_get_drafted_emails", "gmail_send_drafted_email"]:
        raise ValueError("Unknown tool")
    
    return intent

