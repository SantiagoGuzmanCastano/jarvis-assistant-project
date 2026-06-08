
from fastapi import APIRouter, Depends

from app.db.session import SessionDep
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.auth import login_user, register_user
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserRegisterResponse

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