from fastapi import APIRouter, Depends

from app.db.session import SessionDep
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user_settings import UserSettingsCreate, UserSettingsResponse, UserSettingsUpdate
from app.services.user_settings import create_current_user_setting, get_current_user_settings, restart_current_user_settings, update_current_user_settings

router = APIRouter(prefix='/user_settings', tags=['user_settings'])

@router.post('',response_model=UserSettingsResponse)
def create_my_settings(body: UserSettingsCreate, session: SessionDep, current_user: User = Depends(get_current_user)):
    new_user_settings= create_current_user_setting(user_id=current_user.id, session=session, body=body)
    return new_user_settings

@router.patch('', response_model=UserSettingsResponse)
def update_my_settings(body: UserSettingsUpdate, session: SessionDep, current_user: User = Depends(get_current_user)):
    updated_user_settings = update_current_user_settings(user_id=current_user.id, session=session, body=body)
    return updated_user_settings

@router.get('/me', response_model=UserSettingsResponse)
def get_my_settings(session: SessionDep, current_user: User = Depends(get_current_user)):
    user_settings = get_current_user_settings(user_id=current_user.id, session=session)
    return user_settings

@router.patch('/reset', response_model=UserSettingsResponse)
def restart_my_settings(session: SessionDep, current_user: User = Depends(get_current_user)):
    user_settings_restarted = restart_current_user_settings(user_id=current_user.id, session=session)
    return user_settings_restarted