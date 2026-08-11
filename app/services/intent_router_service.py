import logging

from app.integrations.gemini_client import generate_gemini_intent_response
from app.schemas.intent_router import ToolIntent
from app.services.intent_router import build_intent_input, build_tool_intent_prompt
from app.services.intent_router_parser import parse_tool_intent_response


logger = logging.getLogger(__name__)


def detect_tool_intent(last_message_content: str,recent_messages_content_list: list,) -> ToolIntent:

    system_intent_prompt = build_tool_intent_prompt()

    conversation_content = build_intent_input(
        last_message_content=last_message_content,
        recent_messages_content_list=recent_messages_content_list,
    )
    
    tool_response = generate_gemini_intent_response(
        conversation_content=conversation_content,
        system_intent_prompt=system_intent_prompt,
    )

    print("\nCONVERSATION CONTEXT RESPONSE:")
    for message_dict in recent_messages_content_list:
        role = message_dict["role"]
        text = message_dict["parts"][0]["text"]
        print("--------------------------------------------------------")
        print(f"{role}: {text}")
    print("--------------------------------------------------------")
    print("\nRAW TOOL RESPONSE:",)
    print(f"\n{tool_response}")
    print("END RAW TOOL RESPONSE")
    print("\n")

    try:
        return parse_tool_intent_response(response_text=tool_response)
    except ValueError:
        logger.exception("Gemini returned an invalid tool intent.")
        raise
