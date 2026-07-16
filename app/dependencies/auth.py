


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.db.session import SessionDep
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(session: SessionDep, token: str = Depends(oauth2_scheme)):
    user_id = decode_token(token)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token: Could not extract user id")

    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token: User does not exists")

    return user 