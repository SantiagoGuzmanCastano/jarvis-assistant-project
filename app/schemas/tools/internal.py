from typing import Literal

from pydantic import BaseModel

from app.tools.names import ToolName


class ToolsInfoArguments(BaseModel):
    tools: Literal[True]


class ToolInfoItem(BaseModel):
    name: ToolName
    description: str


class ToolsInfoResult(BaseModel):
    tools: list[ToolInfoItem]
    returned_count: int
