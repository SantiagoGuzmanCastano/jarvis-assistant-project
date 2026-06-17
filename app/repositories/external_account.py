
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.external_account import ExternalAccount
from app.schemas.external_account import ExternalAccountResponse



#antes de crear una nueva conexión, preguntar
def get_external_account_by_user_id_and_provider(user_id: int, provider: str, session: Session):
    query = select(ExternalAccount).where(ExternalAccount.user_id == user_id , ExternalAccount.provider == provider)

    return session.scalar(query)


def create_external_account(
        user_id: int,
        provider: str,
        encrypted_access_token: str,
        encrypted_refresh_token: str,
        scopes: str | None,
        session: Session,
        expires_at: datetime | None,
        provider_account_id: str | None = None,
        ) -> ExternalAccount:
    
    new_external_account = ExternalAccount(
        user_id=user_id,
        provider=provider,
        provider_account_id=provider_account_id,
        encrypted_access_token=encrypted_access_token,
        encrypted_refresh_token=encrypted_refresh_token,
        scopes=scopes,
        expires_at=expires_at
    )

    session.add(new_external_account)
    session.commit()
    session.refresh(new_external_account)

    return new_external_account



# Guarda los nuevos tokens de Google en la DB cuando los viejos expiran o cambian
def update_external_account_tokens(
    external_account: ExternalAccount,
    encrypted_access_token: str,
    encrypted_refresh_token: str | None,
    scopes: str | None,
    expires_at: datetime | None,
    session: Session,
    provider_account_id: str | None = None,
) -> ExternalAccount:
    

    external_account.encrypted_access_token = encrypted_access_token

    if encrypted_refresh_token is not None:
        external_account.encrypted_refresh_token = encrypted_refresh_token

    external_account.scopes = scopes
    external_account.expires_at = expires_at
    external_account.provider_account_id = provider_account_id
    external_account.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(external_account)

    return external_account

def list_external_accounts(user_id: int, session: Session):

    query = select(ExternalAccount).where(ExternalAccount.user_id == user_id)

    return session.scalars(query).all()


def delete_external_account(user_id: int, session: Session, provider: str):

    query = delete(ExternalAccount).where(ExternalAccount.user_id == user_id, ExternalAccount.provider == provider)

    session.execute(query)
    session.commit()


