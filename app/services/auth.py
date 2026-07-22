from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings

from app.core.errors import AppError
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token, decode_token, hash_password, hash_refresh_token, verify_password
from app.repositories.refresh_session import create_refresh_session, get_refresh_session_by_token_hash, revoke_active_refresh_sessions_for_user, revoke_refresh_session
from app.repositories.user import create_user, get_user_by_email
from app.schemas.auth import UserLogin, UserRegister

from datetime import datetime, timezone




def register_user(user_info: UserRegister, session: Session):

    user_exists = get_user_by_email(email=user_info.email, session= session)

    if user_exists:
        raise AppError(
            code="user_already_registered",
            message="Email already registered.",
            status_code=400,
        )

    hashed_pw = hash_password(user_info.password)
    user_created = create_user(email= user_info.email, hashed_password=hashed_pw, session= session)
    return user_created


def login_user(user_info: UserLogin, session: Session):

    user_exists = get_user_by_email(email=user_info.email, session= session)
    if user_exists is None:
        raise AppError(
            code="invalid_credentials",
            message="Invalid credentials.",
            status_code=401,
        )
    
    if verify_password(plain_password=user_info.password, hashed_password=user_exists.hashed_password) is False:
        raise AppError(
            code="invalid_credentials",
            message="Invalid credentials.",
            status_code=401,
        )
    
    now = datetime.now(timezone.utc)

    revoke_active_refresh_sessions_for_user(user_id=user_exists.id, session=session, revoked_at=now)

    access_token = create_access_token(user_id=user_exists.id)
    refresh_token = create_refresh_token(user_id=user_exists.id)

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    token_hash = hash_refresh_token(refresh_token=refresh_token)



    create_refresh_session(
        user_id=user_exists.id,
        token_hash=token_hash,
        session=session,
        expires_at=expires_at
    )

    session.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def refresh_user_session(refresh_token: str, session: Session):

    user_id = decode_refresh_token(token=refresh_token)
    token_hash = hash_refresh_token(
    refresh_token=refresh_token,)
    
    if user_id is None:
        raise AppError(
            code="invalid_refresh_token",
            message="The refresh token is invalid or expired.",
            status_code=401,
        )
    
    now = datetime.now(timezone.utc)

    current_session = get_refresh_session_by_token_hash(
        token_hash=token_hash,
        session=session,
    )

    if (
        current_session is None
        or current_session.user_id != user_id
        or current_session.revoked_at is not None
        or now >= current_session.expires_at
    ):
        raise AppError(
            code="invalid_refresh_token",
            message="The refresh token is invalid or expired.",
            status_code=401,
        )

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    
    revoke_refresh_session(token_hash=token_hash,session=session,revoked_at=now)

    new_access_token = create_access_token(user_id=user_id)
    new_refresh_token = create_refresh_token(user_id=user_id)

    create_refresh_session(user_id=user_id, token_hash=hash_refresh_token(new_refresh_token), session=session, expires_at=expires_at)
    session.commit()

    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

def log_user_out(refresh_token: str, session: Session):
    token_hash = hash_refresh_token(
    refresh_token=refresh_token,)

    
    now = datetime.now(timezone.utc)
    
    revoke_refresh_session(token_hash=token_hash,session=session,revoked_at=now)

    session.commit()