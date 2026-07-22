
from fastapi import APIRouter, Depends, status

from app.db.session import SessionDep
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.auth import log_user_out, login_user, refresh_user_session, register_user
from app.schemas.auth import RefreshTokenRequest, RefreshTokenResponse, TokenResponse, UserLogin, UserRegister, UserRegisterResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRegisterResponse)
def user_register(body: UserRegister, session: SessionDep):
    new_user = register_user(user_info=body,session=session)
    return new_user


@router.post("/login", response_model=TokenResponse)
def user_login(body: UserLogin, session: SessionDep):
    response = login_user(user_info=body, session=session)
    return response


@router.get('/me', response_model=UserRegisterResponse)
def user_info(session: SessionDep, current_user: User = Depends(get_current_user)):

    db_user = session.get(User, current_user.id)

    return db_user

@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_access_token(body: RefreshTokenRequest, session: SessionDep):
    return refresh_user_session(refresh_token=body.refresh_token, session=session)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def user_log_out(body: RefreshTokenRequest, session: SessionDep) -> None:
    log_user_out(refresh_token=body.refresh_token, session=session)
