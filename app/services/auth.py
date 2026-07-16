from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user import create_user, get_user_by_email
from app.schemas.auth import UserLogin, UserRegister


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


def login_user(user_info: UserLogin, session: Session):

    user_exists = get_user_by_email(email=user_info.email, session= session)
    if user_exists is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Credentials'
        )
    
    if verify_password(plain_password=user_info.password, hashed_password=user_exists.hashed_password) is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Credentials'
        )
    

    token = create_access_token(user_id=user_exists.id)
    return {"access_token": token, "token_type": "bearer"}
