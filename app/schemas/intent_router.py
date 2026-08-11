from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.tools.names import ToolName


class ToolIntent(BaseModel):
    needs_tool: bool
    tool_name: ToolName | None
    arguments: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_intent_consistency(self):
        if self.needs_tool and self.tool_name is None:
            raise ValueError(
                "tool_name is required when needs_tool is true"
            )

        if not self.needs_tool:
            self.tool_name = None
            self.arguments = {}

        return self
