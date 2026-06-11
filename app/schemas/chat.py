from typing import Literal


from pydantic import BaseModel

class ChatRequest(BaseModel):
    conversation_id: int
    content: str


class ChatResponse(BaseModel):
    role: Literal["assistant"] = "assistant"
    #esto significa que role SOLO puede ser assistant
    content: str