from app.tools.registry import TOOLS


def is_registered_tool(tool_name: str) -> bool:
    return tool_name in TOOLS
