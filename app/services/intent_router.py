
import json

from app.integrations.gemini_client import generate_gemini_intent_response
from app.schemas.intent_router import ToolIntent


def detect_tool_intent(last_message_content: str) -> ToolIntent:
    system_intent_prompt= build_tool_intent_prompt()
    tool_response = generate_gemini_intent_response(last_message_content=last_message_content, system_intent_prompt=system_intent_prompt)

    return parse_tool_intent_response(response_text=tool_response)

    
def build_tool_intent_prompt() -> str:
    return """
You are an intent router for Jarvis.

You do not answer the user directly.
Your only job is to decide whether the user's message should use one of the available backend tools.

Available tools:
- get_current_time: use when the user asks for the current time, current date, today's date, or any time/date-related information.

Rules:
- If an available tool can provide a more accurate, current, or action-based answer, you must select that tool.
- Do not rely on model knowledge when a matching backend tool exists.
- If the user is asking for normal conversation and no available tool matches, do not use a tool.

Return only valid JSON. Do not include markdown. Do not explain anything.

If a tool is needed, return:
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
    
    if intent.tool_name != "get_current_time":
        raise ValueError("Unknown tool")
    
    return intent

