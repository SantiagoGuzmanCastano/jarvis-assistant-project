
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.repositories.user_settings import create_user_settings, delete_user_settings, get_user_settings_by_user_id, update_user_settings_by_user_id
from app.schemas.user_settings import UserSettingsCreate, UserSettingsUpdate


DEFAULT_ASSISTANT_NAME = 'Jarvis'
DEFAULT_ASSISTANT_PERSONALITY = "Loyal, helpful, sharp, direct, and naturally conversational."

def create_current_user_setting(user_id: int, session: Session, body:UserSettingsCreate):

    existing_settings = get_user_settings_by_user_id(user_id=user_id, session=session)

    if existing_settings is not None:
        raise AppError(
            code="user_settings_already_exists",
            message="User settings already exist.",
            status_code=400,
        )
    

    assistant_name= body.assistant_name or DEFAULT_ASSISTANT_NAME
    assistant_personality= body.assistant_personality or DEFAULT_ASSISTANT_PERSONALITY


    new_user_settings = create_user_settings(assistant_name=assistant_name, assistant_personality=assistant_personality, session=session, user_id=user_id, language_mode=body.language_mode)
    return new_user_settings


def update_current_user_settings(user_id: int, session: Session, body: UserSettingsUpdate):

    
    existing_settings = get_user_settings_by_user_id(user_id=user_id, session=session)

    if existing_settings is None:
        raise AppError(
            code="user_settings_not_found",
            message="User settings not found.",
            status_code=404,
        )
    

    updated_data = body.model_dump(exclude_unset=True, exclude_none=True)

    if not updated_data:
        raise AppError(
            code="empty_user_settings_update",
            message="No fields were provided to update.",
            status_code=400,
        )

    return update_user_settings_by_user_id(session=session, user_id=user_id, updated_data=updated_data)

    

def get_current_user_settings(user_id: int, session: Session):
    existing_settings = get_user_settings_by_user_id(user_id=user_id, session=session)

    if existing_settings is None:
        raise AppError(
            code="user_settings_not_found",
            message="User settings not found.",
            status_code=404,
        )
    
    return existing_settings


def restart_current_user_settings(user_id:int, session: Session):

    existing_settings = get_user_settings_by_user_id(user_id=user_id, session=session)

    if existing_settings is None:
        raise AppError(
            code="user_settings_not_found",
            message="User settings not found.",
            status_code=404,
        )
    
    delete_user_settings(user_id=user_id, session=session)
    user_restarted=create_user_settings(user_id=user_id, session=session, assistant_name=DEFAULT_ASSISTANT_NAME, assistant_personality=DEFAULT_ASSISTANT_PERSONALITY, language_mode='auto')

    return user_restarted
