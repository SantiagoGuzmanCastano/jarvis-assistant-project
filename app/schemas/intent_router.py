from pydantic import BaseModel


class ToolIntent(BaseModel):
    needs_tool: bool
    tool_name: str | None
    arguments: dict