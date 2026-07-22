

from datetime import datetime

from sqlalchemy import select, update

from app.models.refresh_session import RefreshSession
from sqlalchemy.orm import Session


def create_refresh_session(user_id:int, token_hash: str, session: Session, expires_at: datetime):
    new_refresh_session = RefreshSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at = expires_at
    )

    session.add(new_refresh_session)
    session.flush()

    return new_refresh_session

def get_refresh_session_by_token_hash(token_hash: str, session: Session):

    query = select(RefreshSession).where(RefreshSession.token_hash==token_hash)
    return session.scalar(query)

def revoke_refresh_session(token_hash: str,session: Session, revoked_at):
    query = update(RefreshSession).where(
        RefreshSession.token_hash == token_hash,
        RefreshSession.revoked_at.is_(None),
    ).values(revoked_at=revoked_at)
    session.execute(query)

def revoke_active_refresh_sessions_for_user(user_id: int, session: Session,revoked_at: datetime):
    query = update(RefreshSession).where(
        RefreshSession.user_id == user_id,
        RefreshSession.revoked_at.is_(None),
    ).values(revoked_at=revoked_at)
    session.execute(query)