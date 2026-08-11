from datetime import datetime

from pydantic import BaseModel, Field

class CreateConversation(BaseModel):
    title: str | None = Field(default=None)

class UpdateConversation(BaseModel):
    title: str = Field(min_length=1, max_length=120)

class DeleteConversation(BaseModel):
    id: int

class CreateMessage(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

#busco devolver solo los datos necesarios para identificar y mostrar una conversacion en una lista
class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime

class ConversationPage(BaseModel):
    items: list[ConversationResponse]
    next_before_id: int | None
    has_more: bool

class ConversationWithMessages(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    messages:list[MessageResponse]
