import json

from app.schemas.intent_router import ToolIntent
from app.services.intent_router_catalog import is_registered_tool


def parse_tool_intent_response(response_text: str) -> ToolIntent:
    raw_intent = json.loads(response_text)
    if not isinstance(raw_intent, dict):
        raise ValueError("Tool intent must be a JSON object")

    if (
        raw_intent.get("needs_tool")
        and not is_registered_tool(raw_intent.get("tool_name"))
    ):
        raise ValueError("Unknown tool")

    intent = ToolIntent.model_validate(raw_intent)

    if not intent.needs_tool:
        return ToolIntent(needs_tool=False, tool_name=None, arguments={})

    return intent
