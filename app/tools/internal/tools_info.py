from sqlalchemy.orm import Session

from app.tools.catalog import TOOL_DESCRIPTIONS


def get_tools_info(
    arguments: dict,
    user_id: int,
    session: Session,
) -> dict:
    from app.tools.registry import TOOLS

    tools = [
        {
            "name": tool_name,
            "description": TOOL_DESCRIPTIONS[tool_name],
        }
        for tool_name in TOOLS
    ]

    return {
        "tools": tools,
        "returned_count": len(tools),
    }
