from fastapi import APIRouter, Depends

from app.db.session import SessionDep
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import create_chat_response

router = APIRouter(prefix='/chat', tags=['chat'])


@router.post('/', response_model=ChatResponse)
def chat_with_jarvis(body: ChatRequest, session: SessionDep, current_user: User = Depends(get_current_user)):
    
    assistant_response = create_chat_response(conversation_id=body.conversation_id, user_id=current_user.id, session=session, content= body.content)

    return assistant_response