import json

from app.schemas.intent_router import ToolIntent
from app.services.intent_router_catalog import is_registered_tool


def parse_tool_intent_response(response_text: str) -> ToolIntent:
    intent = ToolIntent.model_validate(json.loads(response_text))

    if not intent.needs_tool:
        return ToolIntent(needs_tool=False, tool_name=None, arguments={})

    if intent.tool_name is None:
        raise ValueError("tool_name is required when needs_tool is true")

    if not is_registered_tool(intent.tool_name):
        raise ValueError("Unknown tool")

    return intent
