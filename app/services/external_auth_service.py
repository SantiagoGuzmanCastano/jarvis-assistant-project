from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.encryption import decrypt_token, encrypt_token
from app.core.errors import AppError
from app.integrations.google_oauth import exchange_code_for_tokens, get_google_user_info, refresh_google_access_token
from app.repositories.external_account import create_external_account, get_external_account_by_user_id_and_provider, list_external_accounts, update_external_account_tokens


def complete_google_oauth(user_id: int, code: str, session: Session):
    token_data = exchange_code_for_tokens(code=code)

    #token_data DEVUELVE ALGO ASI:
    #{
    #    "access_token": "...",
    #   "expires_in": 3599,
    #    "refresh_token": "...",
    #    "scope": "...",
    #    "token_type": "Bearer"
    #}

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    scopes = token_data.get("scope")
    expires_in = token_data.get("expires_in")

    expires_at = None

    if expires_in is not None:
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    encrypted_access_token = encrypt_token(access_token)

    encrypted_refresh_token = None
    #hay veces que el refresh token no llega
    if refresh_token is not None:
        encrypted_refresh_token = encrypt_token(refresh_token)

    existing_account = get_external_account_by_user_id_and_provider(
        user_id=user_id,
        provider="google",
        session=session,
    )

    google_user_info = get_google_user_info(access_token=access_token)
    provider_account_id = google_user_info.get("email")


    if existing_account is not None:
        return update_external_account_tokens(
            external_account=existing_account,
            provider_account_id=provider_account_id,
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=encrypted_refresh_token,
            scopes=scopes,
            expires_at=expires_at,
            session=session,
        )
    

    return create_external_account(
        user_id=user_id,
        provider="google",
        provider_account_id=provider_account_id,
        encrypted_access_token=encrypted_access_token,
        encrypted_refresh_token=encrypted_refresh_token,
        scopes=scopes,
        expires_at=expires_at,
        session=session,
    )


def get_valid_google_access_token(user_id: int, session: Session):
    external_account=get_external_account_by_user_id_and_provider(user_id=user_id, provider="google", session=session)

    if external_account is None:
        raise AppError(
            code="external_account_not_found",
            message="Google account connection not found.",
            status_code=404,
        )

    #si aun no ha expirado el access_token... todavia es util
    if external_account.expires_at is not None and external_account.expires_at > datetime.now() + timedelta(minutes=1):
        return decrypt_token(external_account.encrypted_access_token)
    
    #si no se encontró
    if external_account.encrypted_refresh_token is None:
        raise AppError(
            code="google_refresh_token_not_found",
            message="Google refresh token not found.",
            status_code=404,
        )

    #si ya expiro el access_token
    refresh_token = decrypt_token(external_account.encrypted_refresh_token)

    #se desencripta y se manda a google para generar uno nuevo
    response = refresh_google_access_token(refresh_token=refresh_token)

    new_access_token = response['access_token']
    expires_in = response.get("expires_in")
    scopes = response.get("scope")

    expires_at = None
    if expires_in is not None:
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    encrypted_access_token=encrypt_token(token=new_access_token)


    update_external_account_tokens(
            external_account=external_account,
            provider_account_id=external_account.provider_account_id,
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=None,
            scopes=scopes,
            expires_at=expires_at,
            session=session,
        )
    
    return new_access_token


def list_current_user_external_accounts(user_id: int, session: Session):
    response = list_external_accounts(user_id=user_id, session=session)

    if not response :
        raise AppError(
            code="external_accounts_not_found",
            message="No external account connections were found.",
            status_code=404,
        )
    
    return response
