
from fastapi import APIRouter

from db.session import SessionDep
from services.auth import register_user
from schemas.auth import UserLogin, UserRegister, UserRegisterResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRegisterResponse)
def user_register(body: UserRegister, session: SessionDep):
    new_user = register_user(user_info=body,session=session)
    return new_user