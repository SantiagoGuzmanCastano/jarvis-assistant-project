from fastapi import APIRouter, Depends

from app.core.oauth_state import create_oauth_state, verify_oauth_state
from app.db.session import SessionDep
from app.dependencies.auth import get_current_user
from app.integrations.google_oauth import build_google_auth_url
from app.models.user import User
from app.repositories.external_account import delete_external_account, list_external_accounts
from app.schemas.external_account import ExternalAccountResponse
from app.services.external_auth_service import complete_google_oauth, get_valid_google_access_token, list_current_user_external_accounts


router = APIRouter(prefix='/external-auth', tags=["external-auth"])

@router.get("/google/connect")
def connect_google(current_user: User = Depends(get_current_user)):
    state = create_oauth_state(user_id=current_user.id)
    auth_url = build_google_auth_url(state=state)

    return {
        "auth_url": auth_url
    }

@router.get("/google/callback", response_model=ExternalAccountResponse)
def google_callback(code: str, state: str, session: SessionDep):
    user_id = verify_oauth_state(state)

    external_account = complete_google_oauth(
        user_id=user_id,
        code=code,
        session=session,
    )

    return external_account


@router.get("/accounts", response_model= list[ExternalAccountResponse])
def get_user_external_accounts(session: SessionDep, current_user: User = Depends(get_current_user)):
    user_external_accounts = list_current_user_external_accounts(session=session, user_id=current_user.id)
    return user_external_accounts
    

@router.delete("/google")
def delete_user_external_accounts(session: SessionDep, current_user: User = Depends(get_current_user)):
    delete_external_account(session=session, user_id=current_user.id, provider='google')
    return
