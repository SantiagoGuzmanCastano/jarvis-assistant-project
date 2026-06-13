from datetime import datetime

from pydantic import BaseModel, Field

class CreateConversation(BaseModel):
    title: str | None = Field(default=None)

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

class ConversationWithMessages(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    messages:list[MessageResponse]