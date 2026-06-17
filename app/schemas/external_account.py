

from datetime import datetime

from pydantic import BaseModel


class ExternalAccountResponse(BaseModel):

    id: int
    user_id: int

    provider: str

    #provider_account_id puede ser None porque Google puede darte primero los tokens y no el email
    provider_account_id: str | None

    scopes: str | None


    # None no significa "nunca expira"
    # significa: "no sabemos si sigue valido"
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime