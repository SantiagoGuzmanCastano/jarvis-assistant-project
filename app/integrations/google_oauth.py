from urllib.parse import urlencode

from app.core.config import settings

import requests

from app.core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_GMAIL_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose"] 



# esta funcion crea la URL a donde mandamos al usuario para que autorice a Jarvis en Google
# solo construye un link
# este link abre la pantalla de google
# Jarvis quiere acceder a tu cuenta
# [ ] Ver tu Gmail
# [ ] Ver tu email

# https://accounts.google.com/o/oauth2/v2/auth
# ?client_id=...
# &redirect_uri=...
# &response_type=code
# &scope=...
# &access_type=offline
# &prompt=consent
def build_google_auth_url(state:str) -> str:

    #estos datos de la URL son instrucciones para Google
    query_params = {

        #quien es tu app en Google Cloud, Esta request viene de Jarvis AI App
        #Google usa esto para saber, que app esta pidiendo permisos
        "client_id": settings.google_client_id,

        #Es la URL de tu backend a donde Google vuelve después de que el usuario acepta.
        "redirect_uri": settings.google_redirect_uri,
        #ejemplo:
        #http://localhost:8000/external-auth/google/callback
        #Flujo:
        #Usuario acepta en google
        #-> Google redirige a redirect_uri
        #-> agrega ?code=...
        #Resultado: http://localhost:8000/external-auth/google/callback?code=abc123
        #Importante: este redirect_uri debe estar registrado exactamente igual en Google Cloud.

        #no me des tokens directamente en el navegador
        #dame un code temporal
        #mi backend luego cambia ese code por tokens
        "response_type": "code",

        #que permisos estamos pidiendo
        #https://www.googleapis.com/auth/gmail.readonly
        #https://www.googleapis.com/auth/userinfo.email
        "scope": " ".join(GOOGLE_GMAIL_SCOPES),

        # quiero poder acceder a las apis de google autorizadas por el usuario
        # cuando el usuario no esta usando la app en la practica queremos refresh_token
        # sin offline, google puede darte solo access_token que expira rapido
        # Para Jarvis necesitamos refresh_token, porque el usuario no debería reconectar Gmail cada hora.
        # access_type=offline permite que Jarvis renueve el access_token con el refresh_token 
        # aunque el usuario no esté en la pantalla de Google en ese momento.
        "access_type": "offline",

        # le dice a Google que siempre muestre la pantalla de consentimiento, 
        # aunque el usuario ya haya autorizado la app antes.
        "prompt": "consent",

        "state": state
        # Para que cuando Google te devuelva al callback, puedas verificar que ese callback lo
        # provocó un flujo que tú iniciaste y no alguien externo mandándote un callback 
        # falso con un code de Google válido pero para otra sesión.
        # Sin el state, tu backend no tiene forma de distinguir un callback legítimo de uno fabricado.
    }

    return f"{GOOGLE_AUTH_URL}?{urlencode(query_params)}"


def exchange_code_for_tokens(code: str) -> dict:
    data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.google_redirect_uri,
    }

    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    response.raise_for_status()

    return response.json()
    #DEVUELVE ALGO ASI:
    #{
    #    "access_token": "...",
    #   "expires_in": 3599,
    #    "refresh_token": "...",
    #    "scope": "...",
    #    "token_type": "Bearer"
    #}


def refresh_google_access_token(refresh_token: str) -> dict:
    data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    response.raise_for_status()

    return response.json()


GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_user_info(access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
    response.raise_for_status()

    return response.json()
    # {
    #   "id": "...",
    #   "email": "usuario@gmail.com",
    #   "verified_email": true
    # }
