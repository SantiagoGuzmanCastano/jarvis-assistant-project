

from sqlalchemy import select,update,delete
from sqlalchemy.orm import Session

from app.models.user_settings import UserSettings


def get_user_settings_by_user_id(user_id:int, session: Session):

    query = select(UserSettings).where(UserSettings.user_id==user_id)
    return session.scalar(query)



def create_user_settings(assistant_name: str, assistant_personality: str, user_id: int, session: Session, language_mode: str):

    new_user_settings = UserSettings(
        user_id=user_id,
        assistant_name=assistant_name,
        assistant_personality=assistant_personality,
        language_mode=language_mode
    )

    session.add(new_user_settings)
    session.commit()
    session.refresh(new_user_settings)

    return new_user_settings


def update_user_settings_by_user_id(updated_data: dict, session: Session, user_id: int):

    query = update(UserSettings).where(UserSettings.user_id==user_id).values(**updated_data)
    session.execute(query)

    session.commit()

    user_settings = get_user_settings_by_user_id(user_id=user_id, session=session)
    return user_settings

def delete_user_settings(user_id: int, session: Session):

    query = delete(UserSettings).where(UserSettings.user_id==user_id)

    session.execute(query)
    session.commit()
    