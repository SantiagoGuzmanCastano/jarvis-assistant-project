from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.security import hash_password
from repositories.user import create_user, get_user_by_email
from schemas.auth import UserRegister


def register_user(user_info: UserRegister, session: Session):

    user_exists = get_user_by_email(email=user_info.email, session= session)

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email already registered'
        )

    hashed_pw = hash_password(user_info.password)
    user_created = create_user(email= user_info.email, hashed_password=hashed_pw, session= session)
    return user_created